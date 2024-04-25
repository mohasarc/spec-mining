#include <Python.h>

// Original append function pointer
static PyObject *(*original_append)(PyObject *, PyObject *);

// New append method
static PyObject *custom_append(PyObject *self, PyObject *arg) {
    // Wrap every appended item with ~~~~
    // PyObject *new_arg = PyUnicode_FromFormat("~~~~%S~~~~", arg);
    // if (new_arg == NULL) return NULL; // Handle error in argument creation

    // Assuming Python's GIL is already held or your context ensures it

    // find the module and function and call it
    PyObject *pName = PyUnicode_FromString("pymop_instrumentation");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "append_python");

        if (pFunc && PyCallable_Check(pFunc)) {
            // Create a tuple containing the argument and the ID of the list instance
            PyObject *args = PyTuple_New(2);
            Py_INCREF(arg); // Increment ref count of arg since PyTuple_SetItem steals a reference
            PyTuple_SetItem(args, 0, arg);

            PyObject *id = PyLong_FromVoidPtr((void*)self); // Get the unique identifier of the object
            PyTuple_SetItem(args, 1, id); // Tuple steals the reference to id

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

    // Call the original append method with the new argument
    PyObject *result = original_append(self, arg);
    // Py_DECREF(new_arg); // Clean up the reference
    return result;
}

// Function to replace the append method of the list type
static PyObject *install_custom_append(PyObject *module) {
    // Find the 'append' method in the list of methods for the list type
    PyMethodDef *methods = PyList_Type.tp_methods;
    for (; methods->ml_name != NULL; methods++) {
        if (strcmp(methods->ml_name, "append") == 0) {
            original_append = (PyObject *(*)(PyObject *, PyObject *))methods->ml_meth;
            methods->ml_meth = (PyCFunction)custom_append;
            break;
        }
    }
    Py_RETURN_NONE;
}

// Module method definitions
static PyMethodDef module_methods[] = {
    {"install_custom_append", install_custom_append, METH_NOARGS, "Patches the list append method."},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef customlistmodule = {
    PyModuleDef_HEAD_INIT,
    "customlist",
    "Module to override list append method.",
    -1,
    module_methods
};

// Initialize the module
PyMODINIT_FUNC PyInit_customlist(void) {
    return PyModule_Create(&customlistmodule);
}
