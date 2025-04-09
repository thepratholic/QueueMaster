document.addEventListener("DOMContentLoaded", function () {
    const personInput = document.getElementById("personInput");
    const insertBtn = document.getElementById("insertBtn");
    const deleteBtn = document.getElementById("deleteBtn");
    const displayBtn = document.getElementById("displayBtn");
    const closeBtn = document.getElementById("closeBtn");
    const queueTableBody = document.querySelector("#queueTable tbody");
    const queueContainer = document.getElementById("queueContainer");
    const toggleSwitch = document.getElementById("darkModeToggle");
    const liveCount = document.getElementById("liveCount");
    const notificationsList = document.getElementById("notificationsList");
    const exportBtn = document.getElementById("exportBtn");
    const helpBtn = document.getElementById("helpBtn");
    const helpModal = document.getElementById("helpModal");
    const closeHelpBtn = document.getElementById("closeHelpBtn");

    // --------------------------
    // Notification Function
    // --------------------------
    function addNotification(type, message, messageType = 'info') {
        const notificationItem = document.createElement('div');
        let typeClass = 'text-blue-600 dark:text-blue-400';
        if (messageType === 'warning') {
            typeClass = 'text-yellow-600 dark:text-yellow-400';
        } else if (type === 'Added') {
            typeClass = 'text-green-600 dark:text-green-400';
        } else if (type === 'Removed') {
            typeClass = 'text-red-600 dark:text-red-400';
        }
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        notificationItem.className = 'flex items-start';
        notificationItem.innerHTML = `
            <span class="inline-block w-16 text-xs text-gray-500 dark:text-gray-400">${timestamp}</span>
            <span class="font-medium ${typeClass} mr-1">${type}:</span>
            <span class="text-gray-700 dark:text-gray-300">${message}</span>
        `;
        notificationsList.prepend(notificationItem);
        const items = notificationsList.children;
        if (items.length > 20) {
            notificationsList.removeChild(items[items.length - 1]);
        }
    }

    // --------------------------
    // Dark Mode Setup
    // --------------------------
    const rootElement = document.documentElement;
    if (localStorage.getItem("darkMode") === "enabled") {
        rootElement.classList.add("dark");
        toggleSwitch.checked = true;
    } else {
        rootElement.classList.remove("dark");
        toggleSwitch.checked = false;
    }
    toggleSwitch.addEventListener("change", function () {
        if (this.checked) {
            rootElement.classList.add("dark");
            localStorage.setItem("darkMode", "enabled");
        } else {
            rootElement.classList.remove("dark");
            localStorage.setItem("darkMode", "disabled");
        }
    });

    // --------------------------
    // Refresh Functions: Queue and Analytics via HTTP polling
    // --------------------------
    function loadQueue() {
        fetch('/display')
            .then(response => response.json())
            .then(data => {
                updateQueueDisplay(data.queue);
                liveCount.textContent = data.queue.length;
            })
            .catch(error => console.error("Error loading queue:", error));
    }

    function fetchAnalytics() {
        fetch('/analytics')
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalServed').textContent = data.total_served;
                document.getElementById('avgWaitTime').textContent = data.avg_wait_time;
            })
            .catch(err => console.error("Error fetching analytics:", err));
    }

    // --------------------------
    // Update Queue Display
    // --------------------------
    function updateQueueDisplay(queueData) {
        queueTableBody.innerHTML = "";
        queueData.forEach((entry, index) => {
            let row = document.createElement("tr");
            row.className = "bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100";

            let indexCell = document.createElement("td");
            indexCell.textContent = index + 1;
            indexCell.className = "p-2 border";

            let nameCell = document.createElement("td");
            nameCell.className = "p-2 border flex items-center";
            let nameSpan = document.createElement("span");
            nameSpan.textContent = entry.person_name;
            nameCell.appendChild(nameSpan);

            // Add a badge if priority is not "normal"
            if (entry.priority && entry.priority.toLowerCase() !== "normal") {
                let badge = document.createElement("span");
                badge.className = "ml-2 inline-block text-xs px-2 py-1 rounded";
                if (entry.priority.toLowerCase() === "urgent") {
                    badge.classList.add("bg-red-500", "text-white");
                    badge.textContent = "Urgent";
                } else if (entry.priority.toLowerCase() === "low") {
                    badge.classList.add("bg-blue-500", "text-white");
                    badge.textContent = "Low";
                } else {
                    badge.classList.add("bg-gray-500", "text-white");
                    badge.textContent = entry.priority;
                }
                nameCell.appendChild(badge);
            }

            row.appendChild(indexCell);
            row.appendChild(nameCell);
            queueTableBody.appendChild(row);
        });
    }

    // --------------------------
    // Insert a Person
    // --------------------------
    insertBtn.addEventListener("click", function () {
        let personName = personInput.value.trim();
        console.log("Attempting to insert:", personName);
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
                console.log("Response status:", status, "Body:", body);
                if (status !== 200) {
                    alert(body.message);
                } else {
                    Toastify({
                        text: `${personName} has been inserted into the queue`,
                        duration: 3000,
                        gravity: "top",
                        position: "right",
                        backgroundColor: "#10B981",
                        stopOnFocus: true
                    }).showToast();
                    addNotification('Added', `${personName} has been inserted into the queue`);
                    loadQueue();
                    fetchAnalytics();
                }
                personInput.value = "";
            });
    });

    // --------------------------
    // Delete the First Person
    // --------------------------
    deleteBtn.addEventListener("click", function () {
        fetch('/delete', { method: 'POST' })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status !== 200) {
                    alert(body.message);
                } else {
                    Toastify({
                        text: body.message,
                        duration: 3000,
                        gravity: "top",
                        position: "right",
                        backgroundColor: "#EF4444",
                        stopOnFocus: true
                    }).showToast();
                    addNotification('Removed', body.message);
                    loadQueue();
                    fetchAnalytics();
                }
            });
    });

    // --------------------------
    // Display and Close Queue Buttons
    // --------------------------
    displayBtn.addEventListener("click", function () {
        showQueue();
    });

    closeBtn.addEventListener("click", function () {
        closeQueue();
    });

    function showQueue() {
        queueContainer.classList.remove("hidden");
        loadQueue();
    }

    function closeQueue() {
        queueContainer.classList.add("hidden");
    }

    // --------------------------
    // Export PDF Functionality with page break handling
    // --------------------------
    if (exportBtn) {
        exportBtn.addEventListener("click", function () {
            console.log("Export button clicked");
            fetch('/analytics')
                .then(response => response.json())
                .then(data => {
                    console.log("Analytics data received:", data);
                    if (!window.jspdf || !window.jspdf.jsPDF) {
                        console.error("jsPDF library is not loaded");
                        alert("Export failed: jsPDF library is not available.");
                        return;
                    }
                    const { jsPDF } = window.jspdf;
                    const doc = new jsPDF();
                    const pageHeight = doc.internal.pageSize.height;
                    
                    // Title and Date
                    doc.setFontSize(20);
                    doc.text("QueueMaster Analytics Report", 105, 20, null, null, "center");
                    doc.setFontSize(12);
                    doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 105, 30, null, null, "center");
                    
                    // Basic Stats
                    doc.setFontSize(14);
                    doc.text("Queue Performance Metrics:", 20, 50);
                    doc.setFontSize(12);
                    doc.text(`Total Customers Served: ${data.total_served}`, 30, 60);
                    doc.text(`Average Wait Time: ${data.avg_wait_time} seconds`, 30, 70);
                    doc.text(`Current Queue Length: ${liveCount.textContent} people`, 30, 80);
                    
                    // Served Customers List
                    let yPos = 90;
                    doc.setFontSize(14);
                    doc.text("Served Customers:", 20, yPos);
                    yPos += 10;
                    
                    if (data.served_details && data.served_details.length > 0) {
                        data.served_details.forEach((cust, index) => {
                            doc.setFontSize(12);
                            if (yPos >= pageHeight - 20) {
                                doc.addPage();
                                yPos = 20;
                            }
                            doc.text(`${index + 1}. Name: ${cust.person_name || "Unknown"}`, 30, yPos);
                            yPos += 6;
                            doc.text(`   Inserted: ${cust.arrival_time || "N/A"}, Served: ${cust.served_time || "N/A"}`, 30, yPos);
                            yPos += 10;
                        });
                    } else {
                        doc.setFontSize(12);
                        doc.text("No served entries found yet.", 30, yPos);
                    }
                    
                    doc.save("QueueMaster-Analytics.pdf");
                })
                .catch(err => {
                    console.error("Error exporting PDF:", err);
                    alert("Export failed due to an error. Please check the console for details.");
                });
        });
    }

    // --------------------------
    // Help Button Feature (if help modal exists in HTML)
    // --------------------------
    if (helpBtn && helpModal && closeHelpBtn) {
        helpBtn.addEventListener("click", function () {
            helpModal.classList.remove("hidden");
        });
        closeHelpBtn.addEventListener("click", function () {
            helpModal.classList.add("hidden");
        });
    }

    // --------------------------
    // Initial load
    // --------------------------
    loadQueue();
    fetchAnalytics();
    addNotification('System', 'Queue system initialized');
});
