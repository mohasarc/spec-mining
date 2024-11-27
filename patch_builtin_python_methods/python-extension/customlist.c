#include <Python.h>

// Original function pointers
static PyObject *(*original_append)(PyObject *, PyObject *);
static int (*original_sort)(PyObject *, PyObject *, PyObject *);

// Reentrancy guards
static int in_custom_append = 0;
static int in_custom_sort = 0;

// New append method
static PyObject *custom_append(PyObject *self, PyObject *arg) {
    if (in_custom_append) {
        return original_append(self, arg);
    }

    in_custom_append = 1;
    PyObject *pName = PyUnicode_FromString("instrumentation");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "append_python");
        if (pFunc && PyCallable_Check(pFunc)) {
            PyObject *args = PyTuple_New(2);
            Py_INCREF(arg);
            PyTuple_SetItem(args, 0, arg);
            PyObject *id = PyLong_FromVoidPtr((void*)self);
            PyTuple_SetItem(args, 1, id);
            PyObject *pValue = PyObject_CallObject(pFunc, args);
            Py_DECREF(args);
            if (pValue != NULL) {
                Py_DECREF(pValue);
            } else {
                PyErr_Print();
            }
        } else {
            PyErr_Print();
        }
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
    }
    in_custom_append = 0;
    PyObject *result = original_append(self, arg);
    return result;
}

// New sort method adapted to handle kwargs properly
static PyObject *custom_sort(PyObject *self, PyObject *args, PyObject *kwargs) {
    if (in_custom_sort) {
        return original_sort(self, args, kwargs); // Direct call to original function
    }

    in_custom_sort = 1;
    PyObject *pName = PyUnicode_FromString("instrumentation");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "sort_python");
        if (pFunc && PyCallable_Check(pFunc)) {
            PyObject *argList = PyTuple_New(1);
            PyObject *id = PyLong_FromVoidPtr((void*)self);
            PyTuple_SetItem(argList, 0, id);
            PyObject *pValue = PyObject_CallObject(pFunc, argList);
            Py_DECREF(argList);
            if (pValue != NULL) {
                Py_DECREF(pValue);
            } else {
                PyErr_Print();
            }
        } else {
            PyErr_Print();
        }
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
    }
    in_custom_sort = 0;
    PyObject *result = original_sort(self, args, kwargs);  // Call the original sort method
    if (!result) {
        return NULL;  // If an error occurred, pass it through
    }
    Py_DECREF(result);
    Py_RETURN_NONE;
}

// Function to replace the append and sort methods of the list type
static PyObject *install_custom_methods(PyObject *module) {
    PyMethodDef *methods = PyList_Type.tp_methods;
    for (; methods->ml_name != NULL; methods++) {
        if (strcmp(methods->ml_name, "append") == 0) {
            original_append = (PyObject *(*)(PyObject *, PyObject *))methods->ml_meth;
            methods->ml_meth = (PyCFunction)custom_append;
        } else if (strcmp(methods->ml_name, "sort") == 0) {
            original_sort = (int (*)(PyObject *, PyObject *, PyObject *))methods->ml_meth;
            methods->ml_meth = (PyCFunction)(void(*)(void))custom_sort;
        }
    }
    Py_RETURN_NONE;
}

// Function to restore the original append and sort methods of the list type
static PyObject *uninstall_custom_methods(PyObject *module) {
    PyMethodDef *methods = PyList_Type.tp_methods;
    for (; methods->ml_name != NULL; methods++) {
        if (strcmp(methods->ml_name, "append") == 0 && (PyCFunction)methods->ml_meth == (PyCFunction)custom_append) {
            methods->ml_meth = (PyCFunction)original_append;
        } else if (strcmp(methods->ml_name, "sort") == 0 && (PyCFunction)methods->ml_meth == (PyCFunction)(void(*)(void))custom_sort) {
            methods->ml_meth = (PyCFunction)original_sort;
        }
    }
    Py_RETURN_NONE;
}

// Module method definitions
static PyMethodDef module_methods[] = {
    {"install_custom_methods", install_custom_methods, METH_NOARGS, "Patches the list append and sort methods."},
    {"uninstall_custom_methods", uninstall_custom_methods, METH_NOARGS, "Restores the original list append and sort methods."},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef customlistmodule = {
    PyModuleDef_HEAD_INIT,
    "customlist",
    "Module to override and restore list append and sort methods.",
    -1,
    module_methods
};

// Initialize the module
PyMODINIT_FUNC PyInit_customlist(void) {
    return PyModule_Create(&customlistmodule);
}
