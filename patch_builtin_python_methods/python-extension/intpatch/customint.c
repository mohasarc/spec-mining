#include <Python.h>

// Pointer to store original tp_new of int type
static newfunc original_int_new;

// Reentrancy guard
static int in_custom_int_new = 0;

// New tp_new function for int type
static PyObject *custom_int_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {
    PyObject *obj = original_int_new(subtype, args, kwds);
    if (!obj) return NULL; // If there's an error, return immediately

    // Check if we are already inside custom_int_new
    if (in_custom_int_new) {
        return obj;
    }

    // Set the reentrancy guard
    in_custom_int_new = 1;

    // Find the module and function to call it
    PyObject *pName = PyUnicode_FromString("pythonmop.instrumentation");
    PyObject *pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (pModule != NULL) {
        PyObject *pFunc = PyObject_GetAttrString(pModule, "int_py");

        if (pFunc && PyCallable_Check(pFunc)) {
            // Create a tuple containing the created int object
            PyObject *args = PyTuple_New(1);
            Py_INCREF(obj); // Increment ref count since PyTuple_SetItem steals a reference
            PyTuple_SetItem(args, 0, obj);

            PyObject *pValue = PyObject_CallObject(pFunc, args); // Call with the tuple as argument
            Py_DECREF(args); // Decrement reference count of args tuple

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

    // Clear the reentrancy guard
    in_custom_int_new = 0;

    return obj;
}

// Function to replace the tp_new of the int type
static PyObject *install_custom_int_new(PyObject *module) {
    // Save the original tp_new and replace it with our custom version
    original_int_new = PyLong_Type.tp_new;
    PyLong_Type.tp_new = (newfunc)custom_int_new;
    Py_RETURN_NONE;
}

// Module method definitions
static PyMethodDef module_methods[] = {
    {"install_custom_int_new", install_custom_int_new, METH_NOARGS, "Patches the int constructor."},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef customintmodule = {
    PyModuleDef_HEAD_INIT,
    "customint",
    "Module to override the int constructor.",
    -1,
    module_methods
};

// Initialize the module
PyMODINIT_FUNC PyInit_customint(void) {
    return PyModule_Create(&customintmodule);
}
