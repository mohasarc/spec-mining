import dotenv from "dotenv";
dotenv.config();

import { Octokit } from '@octokit/core';
import fs from 'fs-extra'
import path from "path";
import { createObjectCsvWriter } from "csv-writer";
import { sleep } from "openai/core";
import { removeRepetition } from "./remove-repetition";
import { sortList } from "../utils/sortList";
import { dependencyNames, specIDList } from "../constants";

const GH_ACCESS_TOKEN = process.env['GH_ACCESS_TOKEN'];
const octokit = new Octokit({ auth: GH_ACCESS_TOKEN });
const MANIFEST_FILES = [
    // "setup.py",
    "requirements",
    // "Pipfile",
    // "Pipfile.lock",
    // "pyproject.toml",
    // "environment.yml",
    // "tox.ini",
    "req.txt",
    "requires"
]

export interface BaseRepository {
    owner: string,
    repoName: string
}

export interface DependantRepoDetails extends BaseRepository {
    repoLink: string,
    stars: number,
    forks: number,
    issues: number,
    pullRequests: number,
    description: string,
    fileName?: string,
    dependencyName: string,
    testingFramework: string,
    created_at: string,
    updated_at: string,
    defaultBranch: string,
    defaultBranchCommitId: string,
    specName?: string
}

export type WithRateLimitMetaData<T> = {
    data: T,
    rateLimitReset?: string,
    remainingRateLimit?: string
}

type Result<T> = {
    data: T,
    ok: true,
    rateLimitReset?: string,
    remainingRateLimit?: string
} | {
    data: null,
    ok: false,
    error: Error,
    rateLimitReset?: string,
    remainingRateLimit?: string
}

const sanitizeValue = (value: string | undefined | number) => {
    if (value == null) {
        return 'N/A'
    }

    if (typeof value === 'number') {
        return value
    }

    // remove any , or ; charachters and replace them with <>
    return value.replace(',', '<>').replace(';', '<>')
}

const supressError = <T>(fn: (...args: any[]) => Promise<T>) => (async (...args: any[]): Promise<T | null> => {
    try {
        return await fn(...args);
    } catch (error) {
        console.error("Error in supressError:", error);
        return null;
    }
})

const formatTimestamp = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');

    return `${year}-${month}-${day}-${hours}-${minutes}-${seconds}`;
}

export const sleepTillRateLimitResets = async (remainingRateLimit?: string, rateLimitReset?: string) => {
    console.log('Rate limit reset:', rateLimitReset, 'Remaining rate limit:', remainingRateLimit);

    if (remainingRateLimit !== undefined && rateLimitReset !== undefined && Number.parseInt(remainingRateLimit) < 2) {
        const currentTime = Math.floor(Date.now() / 1000); // Current time in seconds since epoch
        const delaySeconds = Number.parseInt(rateLimitReset) - currentTime + 10; // Time to wait until reset (10 seconds added to be safe)

        console.log('Rate limit reached, will wait for ', delaySeconds, ' seconds');
        await new Promise(resolve => setTimeout(resolve, delaySeconds * 1000));
        console.log('Resuming after rate limit reset');
    }
}

type QueryFunction<T> = (...args: any[]) => Promise<Result<T>>;
type LimitSafeQueryFunction<T> = (...args: any[]) => Promise<T>;

export const retryOnRateLimitError = <T>(fn: QueryFunction<T>): LimitSafeQueryFunction<T> => async (...args: any[]) => {
    let result = await fn(...args);

    const MAX_RETRIES = 10;

    if (result.ok) {
        return result.data;
    }

    let i = 0;

    while (
        !result.ok &&
        (result.error.message.includes('API rate limit exceeded') || result.error.message.includes('You have exceeded a secondary rate limit'))
    ) {
        if (i >= MAX_RETRIES) {
            console.error('Max retries of ', MAX_RETRIES, ' reached for', args);
            throw result.error;
        }

        const remainingRateLimit = result.remainingRateLimit || '0';
        const rateLimitReset = result.rateLimitReset || `${Math.floor(Date.now() / 1000) + 50}`;
        await sleepTillRateLimitResets(remainingRateLimit, rateLimitReset);
        console.log('Retrying with args', args);
        result = await fn(...args);
        i++;
    }

    if (!result.ok) {
        throw result.error;
    }

    return result.data;
}

const searchForFiles = supressError(retryOnRateLimitError(async (
    fileNames: Array<string>,
    libName: string,
    testingFramework: string,
    page: number
    ): Promise<
        Result<Array<BaseRepository & { fileName: string }>>
    > => {

    try {
        const filePathList = fileNames.map(fileName => `filename:${fileName}`).join("+OR+");
        const searchQuery = `${libName}+${testingFramework}+in:file+${filePathList}`;
        const searchResults = await octokit.request('GET /search/code', {
            q: searchQuery,
            per_page: 100, // Adjust per_page as needed, up to a maximum of 100
            page,
        });
    
        const rateLimitReset = searchResults.headers["x-ratelimit-reset"]
        const remainingRateLimit = searchResults.headers["x-ratelimit-remaining"]


        return {
            ok: true,
            data: searchResults.data.items.map(item => ({
                owner: item.repository.owner.login,
                repoName: item.repository.name,
                fileName: item.name
            })),
            rateLimitReset,
            remainingRateLimit
        };
    } catch (error) {
        const rateLimitReset = (error as any).response.headers["x-ratelimit-reset"]
        const remainingRateLimit = (error as any).response.headers["x-ratelimit-remaining"]

        return {
            data: null,
            ok: false,
            error: error as Error,
            rateLimitReset,
            remainingRateLimit
        }
    }
}))

const searchForRegex = supressError(retryOnRateLimitError(
    async (
        specRegex: string,
        page: number
    ): Promise<
        Result<Array<BaseRepository & { fileName: string }>>
    > => {
    try {
        const searchQuery = `${specRegex}+in:file+language:Python`;

        console.log('Running query:', searchQuery);
        const searchResults = await octokit.request('GET /search/code', {
            q: searchQuery,
            per_page: 100, // Adjust per_page as needed, up to a maximum of 100
            page,
        });

        const rateLimitReset = searchResults.headers["x-ratelimit-reset"]
        const remainingRateLimit = searchResults.headers["x-ratelimit-remaining"]

        return {
            ok: true,
            data: searchResults.data.items.map(item => ({
                owner: item.repository.owner.login,
                repoName: item.repository.name,
                fileName: item.name
            })),
            rateLimitReset,
            remainingRateLimit
        };
    } catch (error) {
        const rateLimitReset = (error as any).response.headers["x-ratelimit-reset"]
        const remainingRateLimit = (error as any).response.headers["x-ratelimit-remaining"]

        return {
            data: null,
            ok: false,
            error: error as Error,
            rateLimitReset,
            remainingRateLimit
        }
    }
}))

const constructRepoDetailsQuery = (repositories: Array<BaseRepository>) => {
    const repoQueries = repositories.map((repo, index) => `
      repo${index}: repositoryOwner(login: "${repo.owner}") {
        repository(name: "${repo.repoName}") {
          description
          forks {
            totalCount
          }
          issues {
            totalCount
          }
          stargazers {
            totalCount
          }
          pullRequests {
            totalCount
          }
          url
          createdAt
          updatedAt
          defaultBranchRef {
            name
            target {
              oid
            }
          }
        }
      }
    `).join('\n');

    // fs.outputFileSync('repoQueries.txt', repoQueries)
  
    // Return the complete query
    return `
      query {
        ${repoQueries}
      }
    `;
}

type ResponseType = {
    [key: string]: {
        repository: {
            description: string,
            forks: {
                totalCount: number
            },
            issues: {
                totalCount: number
            },
            stargazers: {
                totalCount: number
            },
            pullRequests: {
                totalCount: number
            },
            url: string,
            createdAt: string,
            updatedAt: string,
            defaultBranchRef: {
                name: string,
                target: {
                    oid: string
                }
            }
        }
    }
}
 
const fetchRepositoriesDetails = supressError(retryOnRateLimitError(
    async (repositories: Array<BaseRepository>): Promise<
        Result<ResponseType>
    > => {
    try {
        return {
            ok: true,
            data: await octokit.graphql(constructRepoDetailsQuery(repositories))
        };
    } catch (error) {
        const rateLimitReset = (error as any).response.headers["x-ratelimit-reset"]
        const remainingRateLimit = (error as any).response.headers["x-ratelimit-remaining"]

        return {
            data: null,
            ok: false,
            error: error as Error,
            rateLimitReset,
            remainingRateLimit
        }
    }
}))

const saveData = async (outFile: string, data: Array<DependantRepoDetails>) => {
    const fileExists = fs.existsSync(outFile);
    const base = path.dirname(outFile);

    if (!fs.existsSync(base)) {
        fs.mkdirSync(base);
    }

    if (!fileExists) {
        console.log('File Does not exist, creating it', outFile);
    }

    const csvWriterInstance = createObjectCsvWriter({
        path: outFile,
        header: [
            { id: 'owner', title: 'Owner' },
            { id: 'repoName', title: 'Repository Name' },
            { id: 'repoLink', title: 'Repository Link' },
            { id: 'stars', title: 'Stars' },
            { id: 'forks', title: 'Forks' },
            { id: 'issues', title: 'Issues' },
            { id: 'pullRequests', title: 'Pull Requests' },
            { id: 'description', title: 'Description' },
            { id: 'fileName', title: 'File Name' },
            { id: 'dependencyName', title: 'Dependency Name' },
            { id: 'specName', title: 'Spec Name' },
            { id: 'testingFramework', title: 'Testing Framework' },
            { id: 'created_at', title: 'Created At' },
            { id: 'updated_at', title: 'Updated At' },
            { id: 'defaultBranch', title: 'Default Branch' },
            { id: 'defaultBranchCommitId', title: 'Default Branch Commit Id' }
        ],
        append: fileExists
    });

    // escape commas to avoid issues
    await csvWriterInstance.writeRecords(data.map((record) => ({
        description: sanitizeValue(record.description),
        dependencyName: sanitizeValue(record.dependencyName),
        owner: sanitizeValue(record.owner),
        repoName: sanitizeValue(record.repoName),
        repoLink: sanitizeValue(record.repoLink),
        stars: sanitizeValue(record.stars),
        forks: sanitizeValue(record.forks),
        created_at: new Date(record.created_at).toLocaleDateString(),
        fileName: sanitizeValue(record.fileName),
        issues: sanitizeValue(record.issues),
        pullRequests: sanitizeValue(record.pullRequests),
        testingFramework: sanitizeValue(record.testingFramework),
        specName: sanitizeValue(record.specName),
        updated_at: new Date(record.updated_at).toLocaleDateString(),
        defaultBranch: sanitizeValue(record.defaultBranch),
        defaultBranchCommitId: sanitizeValue(record.defaultBranchCommitId)
    })));
}

/**
 * Collect information about python libraries that depend on a given library from GitHub
 */
export const collectGithubRepos = async (outDir: string, testFrameworks: Array<string>, startPage: number, endPage: number, startDependency: number, endDependency: number) => {
    if (endPage > 10) {
        console.warn('End page is greater than 10, which is the maximum number of pages allowed by GitHub code search API. Setting end page to 10');
        endPage = 10;
    }

    const libNames = dependencyNames.slice(startDependency, endDependency);

    const timestamp = Date.now().toString()
    const filePath = path.resolve(outDir, `dependency_based_${timestamp}.csv`)

    const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);
    for (const libName of libNames) {
        for (const file of MANIFEST_FILES) { // this is done to overcome github's limit of 1000 results per search
            for (const testFramework of testFrameworks) {
                for (const page of pages) {
                    console.log('File: ', file, 'Page:', page, ' - Fetching details for', libName, 'from GitHub', 'with test framework:', testFramework);
                    const baseRepoInfo = await searchForFiles([file], libName, testFramework, page)

                    if (!baseRepoInfo) {
                        console.log('No repos found for', libName, 'from GitHub');
                        continue;
                    }
    
                    const chunks = [baseRepoInfo.slice(0, baseRepoInfo.length/2), baseRepoInfo.slice(baseRepoInfo.length/2, baseRepoInfo.length)]
            
                    await Promise.all(chunks.map(async (chunk, i) => {
                        if (chunk.length < 1) return;
    
                        const response = await fetchRepositoriesDetails(chunk);

                        if (!response) {
                            console.log('No response from GitHub for', libName, 'from GitHub');
                            return;
                        }
                    
                        const repoDetails: Array<DependantRepoDetails> = chunk.map((repo, index) => {
                            const repoDetails = response[`repo${index}`]?.repository;

                            if (!repoDetails) {
                                return undefined
                            }

                            return {
                                ...repo,
                                repoLink: repoDetails.url,
                                stars: repoDetails.stargazers.totalCount,
                                forks: repoDetails.forks.totalCount,
                                issues: repoDetails.issues.totalCount,
                                pullRequests: repoDetails.pullRequests.totalCount,
                                description: repoDetails.description,
                                fileName: chunk[index].fileName,
                                dependencyName: libName,
                                testingFramework: testFramework,
                                created_at: repoDetails.createdAt,
                                updated_at: repoDetails.updatedAt,
                                defaultBranch: repoDetails.defaultBranchRef.name,
                                defaultBranchCommitId: repoDetails.defaultBranchRef.target.oid
                            }
                        }).filter(Boolean) as Array<DependantRepoDetails>;
                    
                        console.log('File: ', file, 'Page:', page, ' - ',i + 1, '. Fetched details for', repoDetails.length, 'repos.');
        
                        await saveData(filePath, repoDetails);
                    }))
        
                    await removeRepetition(filePath, 'Repository Link', ['Dependency Name', 'Testing Framework']);
                    const totalRecords = await sortList(filePath, {
                        sortField: 'Stars',
                        customFunction: (a, b) => {
                            // make an array of strings from dep1;dep2;dep3
                            const aStars = Number.parseInt(a['Stars']);
                            const bStars = Number.parseInt(b['Stars']);
                            const aDependencyCount = (a['Dependency Name']?.split('|')?.length || 1) * 10;
                            const bDependencyCount = (b['Dependency Name']?.split('|')?.length || 1) * 10;
                            let result = bDependencyCount * bStars - aDependencyCount * aStars;
    
                            if (result === 0) {
                                result = bStars - aStars;
                            }
                            
                            return result;
                        }
                    });

                    console.log('**************************************************');
                    console.log('Total records so far:  ', totalRecords);
                    console.log('**************************************************');
                }
            }
        }
    }
}

const usesPytest = supressError(retryOnRateLimitError(
    async (
        reposInfo: Array<BaseRepository>
    ): Promise<
        Result<Array<BaseRepository & { usesTestingFramework: boolean }>>
    > => {
        try {
            const filePathList = MANIFEST_FILES.map(fileName => `filename:${fileName}`).join("+OR+");
            const targetPackages = reposInfo.map(repo => `repo:${repo.owner}/${repo.repoName}`).join("+OR+");
            const searchQuery = `${targetPackages}+pytest+in:file+${filePathList}`;
            const searchResults = await octokit.request('GET /search/code', {
                q: searchQuery,
                per_page: 100, // Adjust per_page as needed, up to a maximum of 100
            });

            const rateLimitReset = searchResults.headers["x-ratelimit-reset"]
            const remainingRateLimit = searchResults.headers["x-ratelimit-remaining"]

            const doesUse = searchResults.data.items.map(item => ({
                owner: item.repository.owner.login,
                repoName: item.repository.name
            }));

            return {
                ok: true,
                data: reposInfo.map((repo) => ({
                    ...repo,
                    usesTestingFramework: doesUse.find((item) => item.owner === repo.owner && item.repoName === repo.repoName) !== undefined
                })),
                rateLimitReset,
                remainingRateLimit
            }
        } catch (error) {
            const rateLimitReset = (error as any).response.headers["x-ratelimit-reset"]
            const remainingRateLimit = (error as any).response.headers["x-ratelimit-remaining"]

            return {
                data: null,
                ok: false,
                error: error as Error,
                rateLimitReset,
                remainingRateLimit
            }
        }
}))

export const collectGithubReposUsingSpecs = async (outDir: string, testFrameworks: Array<string>, startPage: number, endPage: number, startSpec: number, endSpec: number) => {
    if (endPage > 10) {
        console.warn('End page is greater than 10, which is the maximum number of pages allowed by GitHub code search API. Setting end page to 10');
        endPage = 10;
    }

    const filePath = path.resolve(outDir, `repos_using_specs_${formatTimestamp()}.csv`)

    const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);
    for (const specId of specIDList.slice(startSpec, endSpec)) {
        for (const testFramework of testFrameworks) {
            for (const page of pages) {
                console.log('Page:', page, ' - Finding repos for spec [', specId.specName, '] from GitHub', 'with test framework:', testFramework);
                const baseRepoInfo = await searchForRegex(specId.githubQuery, page)
                
                if (!baseRepoInfo) {
                    console.log('No repos found for spec [', specId.specName, '] from GitHub');
                    continue;
                }

                console.log('Found', baseRepoInfo.length, 'results previous query from GitHub');

                if (baseRepoInfo.length < 1) {
                    console.log('No repos found for spec [', specId.specName, '] from GitHub');
                    continue;
                }

                // filter out repetitions
                const uniqueBaseRepoInfo = baseRepoInfo.filter((repo, index, self) =>
                    index === self.findIndex((t) => (
                        t.owner === repo.owner && t.repoName === repo.repoName
                    ))
                );
                console.log('Unique repos:', uniqueBaseRepoInfo.length);

                // devide uniqueBaseRepoInfo into n chunks
                const n = 6;
                const chunks = Array.from({ length: n }, (_, i) => uniqueBaseRepoInfo.slice(i * uniqueBaseRepoInfo.length/n, (i + 1) * uniqueBaseRepoInfo.length/n));

                let i = 0;
                for (const chunk of chunks) {
                    if (chunk.length < 1) return;
                    i++;

                    const data = await usesPytest(chunk);

                    if (!data) {
                        console.log('No data from GitHub for', specId.specName, 'from GitHub');
                        continue;
                    }

                    console.log('Chunk:', i, ' - Found', data.filter(repo => repo.usesTestingFramework).length, 'repos out of ', data.length, 'repos that use pytest.');
                    const filteredBaseRepoInfo = data.filter(repo => repo.usesTestingFramework);

                    if (filteredBaseRepoInfo.length < 1)
                        continue;

                    const response = await fetchRepositoriesDetails(filteredBaseRepoInfo);

                    if (!response) {
                        console.log('No response from GitHub for', specId.specName, 'from GitHub');
                        continue;
                    }
                
                    const repoDetails: Array<DependantRepoDetails> = filteredBaseRepoInfo.map((repo, index) => {
                        const details = response[`repo${index}`].repository;
                        return {
                            ...repo,
                            repoLink: details.url,
                            stars: details.stargazers.totalCount,
                            forks: details.forks.totalCount,
                            issues: details.issues.totalCount,
                            pullRequests: details.pullRequests.totalCount,
                            description: details.description,
                            fileName: chunk[index].fileName,
                            dependencyName: specId.dependencyName,
                            testingFramework: testFramework,
                            created_at: details.createdAt,
                            updated_at: details.updatedAt,
                            specName: specId.specName,
                            defaultBranch: details.defaultBranchRef.name,
                            defaultBranchCommitId: details.defaultBranchRef.target.oid
                        }
                    });

                    await saveData(filePath, repoDetails);
                }

                await removeRepetition(filePath, 'Repository Link', ['Spec Name', 'Dependency Name']);
                const totalRecords = await sortList(filePath, {
                    sortField: 'Stars',
                    customFunction: (a, b) => {
                        // make an array of strings from dep1;dep2;dep3
                        const aStars = Number.parseInt(a['Stars']);
                        const bStars = Number.parseInt(b['Stars']);
                        const aDependencyCount = (a['Spec Name']?.split('|')?.length || 1) * 10;
                        const bDependencyCount = (b['Spec Name']?.split('|')?.length || 1) * 10;
                        let result = bDependencyCount * bStars - aDependencyCount * aStars;

                        if (result === 0) {
                            result = bStars - aStars;
                        }
                        
                        return result;
                    }
                });

                console.log('**************************************************');
                console.log('Total records so far:  ', totalRecords);
                console.log('**************************************************');
            }
        }
    }
}
