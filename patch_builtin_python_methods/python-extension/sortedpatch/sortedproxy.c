#include <Python.h>

// Global reference to the built-in sorted function
static PyObject *sorted_func = NULL;

// Function to call the built-in sorted function directly
static PyObject *sorted_wrapper(PyObject *self, PyObject *args, PyObject *kwds) {
    if (!sorted_func) {
        PyErr_SetString(PyExc_RuntimeError, "sorted function not initialized.");
        return NULL;
    }

    // Call the sorted function with the arguments and keywords provided
    PyObject *result = PyObject_Call(sorted_func, args, kwds);

    // Find the module and function to call it
    PyObject *pName = PyUnicode_FromString("pythonmop.instrumentation");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "sorted_py");

        if (pFunc && PyCallable_Check(pFunc)) {

            PyObject *pValue = PyObject_CallObject(pFunc, NULL); // Call with the tuple as argument
            
            if (pValue != NULL) {
                Py_DECREF(pValue);
            } else {
                PyErr_Print(); // Handle error appropriately
            }
        } else {
            PyErr_Print();
        }

        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
    }



    return result;
}

// Method definition for this module
static PyMethodDef SortedProxyMethods[] = {
    {"sorted", (PyCFunction)sorted_wrapper, METH_VARARGS | METH_KEYWORDS, "Custom sorted function that replaces built-in sorted."},
    {NULL, NULL, 0, NULL}  // Sentinel
};

// Module initialization function
static int sortedproxy_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(sorted_func);
    return 0;
}

static int sortedproxy_clear(PyObject *m) {
    Py_CLEAR(sorted_func);
    return 0;
}

static void sortedproxy_free(void *m) {
    sortedproxy_clear((PyObject *)m);
}

// Module definition
static struct PyModuleDef sortedproxymodule = {
    PyModuleDef_HEAD_INIT,
    "sortedproxy",
    NULL,  // Module documentation
    -1,    // Module keeps state in global variables
    SortedProxyMethods,
    NULL,  // Reload
    sortedproxy_traverse,
    sortedproxy_clear,
    sortedproxy_free
};

// Initialization function for this module
PyMODINIT_FUNC PyInit_sortedproxy(void) {
    PyObject *m = PyModule_Create(&sortedproxymodule);
    if (m == NULL) return NULL;

    // Initialize the sorted_func global variable
    sorted_func = PyObject_GetAttrString(PyImport_ImportModule("builtins"), "sorted");
    if (sorted_func == NULL) {
        Py_DECREF(m);
        return NULL;
    }

    PyObject *builtins = PyImport_ImportModule("builtins");
    if (!builtins) {
        Py_DECREF(m);
        return NULL;
    }

    // Get the function definition for sorted_wrapper
    PyObject *sorted_wrapper_func = PyCFunction_New(&SortedProxyMethods[0], NULL);
    if (sorted_wrapper_func == NULL) {
        Py_DECREF(m);
        return NULL;
    }

    // Replace the built-in sorted with sorted_wrapper
    if (PyObject_SetAttrString(builtins, "sorted", sorted_wrapper_func) != 0) {
        Py_DECREF(sorted_wrapper_func);
        Py_DECREF(m);
        return NULL;
    }

    Py_DECREF(sorted_wrapper_func);  // Decrease reference count after setting attribute

    return m;
}
