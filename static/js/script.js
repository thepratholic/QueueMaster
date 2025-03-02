document.addEventListener("DOMContentLoaded", function () {
    const personInput = document.getElementById("personInput");
    const insertBtn = document.getElementById("insertBtn");
    const deleteBtn = document.getElementById("deleteBtn");
    const displayBtn = document.getElementById("displayBtn");
    const closeBtn = document.getElementById("closeBtn");
    const queueTableBody = document.querySelector("#queueTable tbody");
    const queueContainer = document.getElementById("queueContainer");
    const toggleSwitch = document.getElementById("darkModeToggle");
    
    // For Tailwind dark mode, toggle the 'dark' class on the <html> element.
    const rootElement = document.documentElement;

    // Dark Mode Setup: check localStorage and update the root element accordingly.
    if (localStorage.getItem("darkMode") === "enabled") {
        rootElement.classList.add("dark");
        toggleSwitch.checked = true;
        console.log("Dark mode is enabled on load");
    } else {
        rootElement.classList.remove("dark");
        toggleSwitch.checked = false;
        console.log("Dark mode is disabled on load");
    }

    toggleSwitch.addEventListener("change", function () {
        console.log("Toggle changed. Checked:", this.checked);
        if (this.checked) {
            rootElement.classList.add("dark");
            localStorage.setItem("darkMode", "enabled");
            console.log("Dark mode turned on");
        } else {
            rootElement.classList.remove("dark");
            localStorage.setItem("darkMode", "disabled");
            console.log("Dark mode turned off");
        }
    });

    // Insert a person into the queue
    insertBtn.addEventListener("click", function () {
        let personName = personInput.value.trim();
        if (!personName) {
            alert("Please enter a valid name.");
            return;
        }
        fetch('/insert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ 'element': personName })
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status !== 200) {
                alert(body.message);
            }
            personInput.value = "";
            updateAnalytics();
            if (!queueContainer.classList.contains("hidden")) {
                updateQueue();
            }
        });
    });

    // Delete the first person from the queue
    deleteBtn.addEventListener("click", function () {
        fetch('/delete', { method: 'POST' })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status !== 200) {
                alert(body.message);
            }
            updateAnalytics();
            if (!queueContainer.classList.contains("hidden")) {
                updateQueue();
            }
        });
    });

    // Display Queue
    displayBtn.addEventListener("click", function () {
        showQueue();
    });

    // Close Queue
    closeBtn.addEventListener("click", function () {
        closeQueue();
    });

    function showQueue() {
        queueContainer.classList.remove("hidden");
        updateQueue();
    }

    function closeQueue() {
        queueContainer.classList.add("hidden");
    }

    function updateQueue() {
        fetch('/display')
            .then(response => response.json())
            .then(data => {
                queueTableBody.innerHTML = "";
                data.queue.forEach((person, index) => {
                    let row = document.createElement("tr");
                    row.className = "bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100";

                    let indexCell = document.createElement("td");
                    indexCell.textContent = index + 1;
                    indexCell.className = "p-2 border";

                    let nameCell = document.createElement("td");
                    nameCell.textContent = person;
                    nameCell.className = "p-2 border";

                    row.appendChild(indexCell);
                    row.appendChild(nameCell);
                    queueTableBody.appendChild(row);
                });
            });
    }

    function updateAnalytics() {
        fetch('/analytics')
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalServed').textContent = data.total_served;
                document.getElementById('avgWaitTime').textContent = data.avg_wait_time;
            });
    }

    // Initialize the app
    updateAnalytics();
    
    // Export PDF functionality
    const exportBtn = document.getElementById("exportBtn");
    if (exportBtn) {
        exportBtn.addEventListener("click", function() {
            fetch('/analytics')
                .then(response => response.json())
                .then(data => {
                    const { jsPDF } = window.jspdf;
                    const doc = new jsPDF();
                    
                    // Add title
                    doc.setFontSize(20);
                    doc.text("QueueMaster Analytics Report", 105, 20, null, null, "center");
                    
                    // Add date
                    doc.setFontSize(12);
                    doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 105, 30, null, null, "center");
                    
                    // Add data
                    doc.setFontSize(14);
                    doc.text("Queue Performance Metrics:", 20, 50);
                    
                    doc.setFontSize(12);
                    doc.text(`Total Customers Served: ${data.total_served}`, 30, 60);
                    doc.text(`Average Wait Time: ${data.avg_wait_time} seconds`, 30, 70);
                    
                    // Save PDF
                    doc.save("QueueMaster-Analytics.pdf");
                });
        });
    }
});