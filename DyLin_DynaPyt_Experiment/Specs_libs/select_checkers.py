from pathlib import Path
import fire

here = Path(__file__).parent.resolve()

issue_codes = {
    "PC-03": {
        "name": "WrongTypeAdded",
        "analysis": "dylin.analyses.WrongTypeAddedAnalysis.WrongTypeAddedAnalysis",
        "aliases": ["A-11"],
    },
    "PC-04": {
        "name": "ChangeListWhileIterating",
        "analysis": "dylin.analyses.ChangeListWhileIterating.ChangeListWhileIterating",
        "aliases": ["A-22"],
    },
    "PC-05": {
        "name": "ItemInList",
        "analysis": "dylin.analyses.ItemInListAnalysis.ItemInListAnalysis",
        "aliases": [],
    },
    "PC-06": {
        "name": "FilesClosed",
        "analysis": "dylin.analyses.FilesClosedAnalysis.FilesClosedAnalysis",
        "aliases": ["A-08"],
    },
    "SL-01": {
        "name": "InPlaceSort",
        "analysis": "dylin.analyses.InPlaceSortAnalysis.InPlaceSortAnalysis",
        "aliases": ["A-09"],
    },
    "SL-02": {
        "name": "AnyAllMisuse",
        "analysis": "dylin.analyses.BuiltinAllAnalysis.BuiltinAllAnalysis",
        "aliases": ["A-21"],
    },
    "SL-03": {
        "name": "StringStrip",
        "analysis": "dylin.analyses.StringStripAnalysis.StringStripAnalysis",
        "aliases": ["A-19", "A-20"],
    },
    "SL-04": {
        "name": "StringConcat",
        "analysis": "dylin.analyses.StringConcatAnalysis.StringConcatAnalysis",
        "aliases": ["A-05"],
    },
}


def select_checkers(include: str = "all", exclude: str = "none", output_dir: str = None) -> str:
    if include is None:
        include = "none"
    if exclude is None:
        exclude = "none"
    if include.lower() == "all" and exclude.lower() == "none":
        res = "\n".join([issue["analysis"] for _, issue in issue_codes.items()])
    elif include.lower() == "all":
        res = "\n".join(
            [
                issue["analysis"]
                for code, issue in issue_codes.items()
                if (code not in exclude and issue["name"] not in exclude)
            ]
        )
    elif exclude.lower() == "none":
        res = "\n".join(
            [issue["analysis"] for code, issue in issue_codes.items() if (code in include or issue["name"] in include)]
        )
    else:
        res = "\n".join(
            [
                issue["analysis"]
                for code, issue in issue_codes.items()
                if (code in include or issue["name"] in include)
                and (code not in exclude and issue["name"] not in exclude)
            ]
        )
    if output_dir is not None:
        return "\n".join([f"{ana};output_dir={output_dir}" for ana in res.split("\n")])
    return res


if __name__ == "__main__":
    fire.Fire(select_checkers)
