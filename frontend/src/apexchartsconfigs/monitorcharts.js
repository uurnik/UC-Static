const radialCPUoptions = {
  chartOptions: {
    labels: ["Availability"],
    title: {
      align: "center",
      style: {
        fontSize: "14px",
        fontWeight: "bold",
        fontFamily: "Roboto,sans-serif",
        color: "#42A5F5",
      },
    },
    colors: ["#42A5F5"],
    // fill:{
    //   type: 'solid',
    //   colors: ['#EF5350']
    // },
    chart: {
      height: 200,
      type: "radialBar",
    },
    plotOptions: {
      radialBar: {
        hollow: {
          size: "70%",
        },
      },
    },
  }
}

const radialMemoryoptions = {
  chartOptions: {
    labels: ["Packet Loss"],
    title: {
      align: "center",
      style: {
        fontSize: "14px",
        fontWeight: "bold",
        fontFamily: "Roboto,sans-serif",
        color: "#42A5F5",
      },
    },
    colors: ["#42A5F5"],
    chart: {
      height: 200,
      type: "radialBar",
    },
    plotOptions: {
      radialBar: {
        hollow: {
          size: "70%",
        },
      },
    },
  }
}


const WANChartOptions = {
  chartOptions: {
    stroke: {
      width: 2.5,
      curve: 'smooth'
    },
    title: {
      text: "WAN Interface",
      align: "center",
      style: {
        fontSize: "17px",
        fontWeight: "medium",
        fontFamily: "Roboto,sans-serif",
        color: "#42A5F5",
      },
    },
    colors: ["#42A5F5"],
    plotOptions: {
      radialBar: {
        hollow: {
          size: "78%",
        },
      },
    },
  },
}



export { radialCPUoptions, radialMemoryoptions,
         WANChartOptions }