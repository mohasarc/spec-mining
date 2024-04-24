#define _GNU_SOURCE
#include <Python.h>
#include <dlfcn.h>
#include <stdio.h>

// Function pointer to hold the original PyList_Append
static int (*original_PyList_Append)(PyObject *, PyObject *);

// Custom PyList_Append implementation
int PyList_Append(PyObject *self, PyObject *item) {
    // Check if the item can be converted to a string
    if (PyUnicode_Check(item)) {
        // Convert the item to a string and print it
        PyObject *item_str = PyObject_Str(item);
        if (item_str != NULL) {
            const char *item_cstr = PyUnicode_AsUTF8(item_str);
            if (item_cstr != NULL) {
                printf("hellooo there %s\n", item_cstr);
            }
            Py_DECREF(item_str);
        }
    }

    // Call the original PyList_Append
    return original_PyList_Append(self, item);
}

// Initializer
void _init(void) {
    printf("Custom PyList_Append loaded.\n");

    // Resolve the original PyList_Append function using dlsym
    original_PyList_Append = (int (*)(PyObject *, PyObject *))dlsym(RTLD_NEXT, "PyList_Append");
    if (!original_PyList_Append) {
        fprintf(stderr, "Failed to hook 'PyList_Append': symbol not found.\n");
    }
}

// 1. Compile with: gcc -Wall -fPIC -DPIC -c listappendhack.c -I/usr/include/python3.8
// 2. run ld -shared -o listappendhack.so listappendhack.o -ldl
// 3. install a python version that's dynamically linked (built with --enable-shared). (e.g. python3.10 from here https://github.com/mohasarc/spec-mining/releases/tag/python3-10-9-build-8816296669)
// 4. run: LD_PRELOAD=./listappendhack.so /usr/local/bin/python3.10 ./listappend.py