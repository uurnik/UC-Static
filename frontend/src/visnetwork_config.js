export const Options = {
    edges: {
        physics: false,
        width: 0.30,
        smooth: true,
        color: "black"
    },
    nodes: {
        // fixed:true,
    },
    // animation: { // animation object, can also be Boolean
    //     duration: 1000, // animation duration in milliseconds (Number)
    //     easingFunction: "easeInOutQuad" // Animation easing function, available are:
    // },

    width: "100%",
    height: "100%",
    physics: {
        enabled: true,
        barnesHut: {
            gravitationalConstant: -11000,
            centralGravity: 0.5,
            springLength: 150,
            springConstant: 0.1,
            damping: 0.8,
            avoidOverlap: 80,
        },
        stabilization: {
            enabled: true,
            iterations: 2000,
            updateInterval: 50,
            onlyDynamicEdges: false,
            fit: true
        }
    },
    interaction: { hover: true, hoverConnectedEdges: true },
    layout: {
        randomSeed: 4,
    },
}