document.addEventListener("DOMContentLoaded", function () {
  // === Orders by Transit Status Chart ===
  const transitCtx = document.getElementById("transitStatusChart").getContext("2d");
  new Chart(transitCtx, {
    type: "bar",
    data: {
      labels: ["In Process", "En Route", "Arrived"],
      datasets: [{
        label: "Orders",
        data: [15, 22, 10],
        backgroundColor: ["#facc15", "#38bdf8", "#34d399"],
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  // === SLA Compliance Chart ===
  const slaCtx = document.getElementById("slaChart").getContext("2d");
  new Chart(slaCtx, {
    type: "doughnut",
    data: {
      labels: ["On Time", "Late"],
      datasets: [{
        label: "SLA",
        data: [82, 18],
        backgroundColor: ["#10b981", "#ef4444"],
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });

  // === Stock Turnover Chart ===
  const stockCtx = document.getElementById("stockTurnoverChart").getContext("2d");
  new Chart(stockCtx, {
    type: "line",
    data: {
      labels: ["January", "February", "March", "April", "May"],
      datasets: [{
        label: "Avg Days in Stock",
        data: [22, 18, 20, 17, 14],
        borderColor: "#60a5fa",
        backgroundColor: "rgba(96, 165, 250, 0.3)",
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
});

// === Transit Efficiency Chart (dynamic from API) ===
fetch("/analytics/api/transit_efficiency")
  .then(res => res.json())
  .then(data => {
    const labels = Object.keys(data);
    const values = Object.values(data);

    const efficiencyCtx = document.getElementById("transitEfficiencyChart").getContext("2d");

    new Chart(efficiencyCtx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Avg Delivery Time (Days)",
          data: values,
          backgroundColor: "#4f46e5",
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: {
            display: true,
            text: "Transit Efficiency by Transport Type"
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Days"
            }
          }
        }
      }
    });
  })
  .catch(err => {
    console.error("Transit Efficiency chart failed to load", err);
  });

