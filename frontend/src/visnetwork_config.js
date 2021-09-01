export const Options = {
    edges: {
        physics: false,
        width: 1,
        smooth: true,
        color: {
            color:"#42A5F5",
            inherit: false,
            highlight: "#42A5F5",
            hover: '#42A5F5',
            opacity:1.0
        },
        hoverWidth:0.9
    },
    nodes: {
    },
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