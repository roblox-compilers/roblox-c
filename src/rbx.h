/*
* rbx.h
* Roblox bindings for C++ and C
* Install using `rcc install rbxc`
* @AsynchronousAI
*/

/*
* This header file defines many macros to speed up Roblox development.
* and it also defines roblox objects for the roblox-c GCC checker
* to not throw errors.
*/

/** ENTER */
/* C++ & C saftey */
#ifdef __cplusplus /**/
extern "C" { /**/
#endif /**/

/* disable compiler warnings */
#pragma GCC diagnostic push /**/
#pragma GCC diagnostic ignored "-Wundefined-internal" /**/
#pragma GCC diagnostic ignored "-Wextern-c-compat" /**/
#pragma GCC diagnostic ignored "-Wexcess-initializers" /**/

/********************/
/*** DEFINITIONS ***/
/********************/
#ifdef RBXCHECK /* being checked, define all macros */
/* functions */
static void print(const char* str, ...);
static void warn(const char* str);
static void error(const char* str);
static void printf(const char* str, ...);

/* macros */
#define export(void)

/* types */
typedef struct {
    int x;
    int y;
} Vector2;
typedef struct {
    int x;
    int y;
    int z;
} Vector3;

#else /* undergoing compilation */
#define RBX 1 /* tell source code that RBX compiler is being used */
#endif
/********************/




/** EXIT */
/* renable compiler warnings */
#pragma GCC diagnostic pop /**/


/* C++ & C saftey */
#ifdef __cplusplus /**/
} /**/
#endif /**/