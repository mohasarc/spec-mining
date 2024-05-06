#include <Python.h>

// Original function pointers
static destructor original_float_dealloc;
static reprfunc original_float_repr;
static hashfunc original_float_hash;
static richcmpfunc original_float_richcompare;
static PyObject *(*original_float_new)(PyTypeObject *, PyObject *, PyObject *);
static PyObject *(*original_float_str)(PyObject *);
static PyObject *(*original_float_getattro)(PyObject *, PyObject *);
static int (*original_float_setattro)(PyObject *, PyObject *, PyObject *);

// Custom implementations with logging and delegating to original functions
static void custom_float_dealloc(PyObject *self) {
    printf("Hello from float_dealloc\n");
    original_float_dealloc(self);
}

static PyObject *custom_float_repr(PyObject *self) {
    printf("Hello from float_repr\n");
    return original_float_repr(self);
}

static Py_hash_t custom_float_hash(PyObject *self) {
    printf("Hello from float_hash\n");
    return original_float_hash(self);
}

static PyObject *custom_float_richcompare(PyObject *self, PyObject *other, int op) {
    printf("Hello from float_richcompare\n");
    return original_float_richcompare(self, other, op);
}

static PyObject *custom_float_new(PyTypeObject *subtype, PyObject *args, PyObject *kwds) {
    printf("Hello from float_new\n");
    // Custom handling of float creation
    PyObject *obj = NULL;
    if (PyTuple_Size(args) == 0) {
        obj = PyFloat_FromDouble(0.0);
    } else {
        PyObject *arg = PyTuple_GetItem(args, 0);
        if (PyUnicode_Check(arg)) {
            obj = PyFloat_FromString(arg);
        } else {
            obj = PyNumber_Float(arg);
        }
    }
    if (obj == NULL) return NULL; // Fallback to the original behavior on failure
    return obj;
}

static PyObject *custom_float_str(PyObject *self) {
    printf("Hello from float_str\n");
    return original_float_str(self);
}

static PyObject *custom_float_getattro(PyObject *self, PyObject *attr_name) {
    printf("Hello from float_getattro\n");
    return original_float_getattro(self, attr_name);
}

static int custom_float_setattro(PyObject *self, PyObject *attr_name, PyObject *value) {
    printf("Hello from float_setattro\n");
    return original_float_setattro(self, attr_name, value);
}

// Function to install custom methods
static int install_custom_float_methods(void) {
    original_float_dealloc = PyFloat_Type.tp_dealloc;
    original_float_repr = PyFloat_Type.tp_repr;
    original_float_hash = PyFloat_Type.tp_hash;
    original_float_richcompare = PyFloat_Type.tp_richcompare;
    original_float_new = PyFloat_Type.tp_new;
    original_float_str = PyFloat_Type.tp_str;
    original_float_getattro = PyFloat_Type.tp_getattro;
    original_float_setattro = PyFloat_Type.tp_setattro;

    PyFloat_Type.tp_dealloc = custom_float_dealloc;
    PyFloat_Type.tp_repr = custom_float_repr;
    PyFloat_Type.tp_hash = custom_float_hash;
    PyFloat_Type.tp_richcompare = custom_float_richcompare;
    PyFloat_Type.tp_new = custom_float_new;
    PyFloat_Type.tp_str = custom_float_str;
    PyFloat_Type.tp_getattro = custom_float_getattro;
    PyFloat_Type.tp_setattro = custom_float_setattro;

    return 0; // Return success
}

// Module definition
static struct PyModuleDef customfloatmodule = {
    PyModuleDef_HEAD_INIT,
    "customfloat",
    "Module to override all float methods with custom implementations.",
    -1,
    NULL, NULL, NULL, NULL, NULL
};

// Initialize the module
PyMODINIT_FUNC PyInit_customfloat(void) {
    PyObject *m = PyModule_Create(&customfloatmodule);
    if (m == NULL) {
        return NULL;
    }

    if (install_custom_float_methods() != 0) {
        return NULL; // Handle error appropriately
    }

    return m;
}
