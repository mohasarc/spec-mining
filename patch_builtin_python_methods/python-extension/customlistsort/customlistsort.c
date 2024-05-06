#include <Python.h>

// Pointer to store the original sort function
static int (*original_list_sort)(PyObject *);

// Wrapper function to intercept calls to list.sort
static int custom_list_sort(PyObject *self) {
    printf("custom_list_sort called\n"); // Custom logging before calling the original function

    // Assuming Python's GIL is already held or your context ensures it

    // Find the module and function and call it
    PyObject *pName = PyUnicode_FromString("pythonmop.instrumentation");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "sort_python");

        if (pFunc && PyCallable_Check(pFunc)) {
            // Create a tuple containing the ID of the list instance
            PyObject *args = PyTuple_New(1);

            PyObject *id = PyLong_FromVoidPtr((void*)self); // Get the unique identifier of the object
            PyTuple_SetItem(args, 0, id); // Tuple steals the reference to id

            PyObject *pValue = PyObject_CallObject(pFunc, args);  // Call with the tuple as argument
            Py_DECREF(args);  // Decrement reference count of args tuple

            if (pValue != NULL) {
                Py_DECREF(pValue);
            } else {
                PyErr_Print();  // Handle error appropriately
            }
        } else {
            PyErr_Print();
        }

        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
    } else {
        PyErr_Print();
    }

    // Call the original sort method
    int result = original_list_sort(self);
    return result;
}

// Function to install the custom sort method
static PyObject *install_custom_list_sort(PyObject *module) {
    // Find the 'sort' method in the list of methods for the list type
    PyMethodDef *methods = PyList_Type.tp_methods;
    for (; methods->ml_name != NULL; methods++) {
        if (strcmp(methods->ml_name, "sort") == 0) {
            original_list_sort = (int (*)(PyObject *))methods->ml_meth;
            methods->ml_meth = (PyCFunction)custom_list_sort;
            break;
        }
    }
    Py_RETURN_NONE;
}

// Function to restore the original sort method
static PyObject *uninstall_custom_list_sort(PyObject *module) {
    // Find the 'sort' method in the list of methods for the list type
    PyMethodDef *methods = PyList_Type.tp_methods;
    for (; methods->ml_name != NULL; methods++) {
        if (strcmp(methods->ml_name, "sort") == 0) {
            if ((PyCFunction)methods->ml_meth == (PyCFunction)custom_list_sort) {
                methods->ml_meth = (PyCFunction)original_list_sort; // Restore original method
            }
            break;
        }
    }
    Py_RETURN_NONE;
}

// Module method definitions
static PyMethodDef module_methods[] = {
    {"install_custom_list_sort", install_custom_list_sort, METH_NOARGS, "Patches the list sort method."},
    {"uninstall_custom_list_sort", uninstall_custom_list_sort, METH_NOARGS, "Restores the original list sort method."},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef customlistsortmodule = {
    PyModuleDef_HEAD_INIT,
    "customlistsort",
    "Module to override and restore list sort method.",
    -1,
    module_methods
};

// Initialize the module
PyMODINIT_FUNC PyInit_customlistsort(void) {
    return PyModule_Create(&customlistsortmodule);
}
