export function beginRequest(
    requestControllers,
    name
) {
    if (requestControllers.current[name]) {
        requestControllers.current[name].abort();
    }

    const controller = new AbortController();

    requestControllers.current[name] = controller;

    return controller;
}

export function isCurrentRequest(
    requestControllers,
    requestGeneration,
    name,
    controller,
    generation
) {
    return (
        requestControllers.current[name] ===
        controller &&
        requestGeneration.current ===
        generation
    );
}

export function isSameRequest(
    requestControllers,
    name,
    controller
) {
    return (
        requestControllers.current[name] ===
        controller
    );
}