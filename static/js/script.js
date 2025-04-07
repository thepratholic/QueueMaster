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

    // Help Modal Elements
    const helpBtn = document.getElementById("helpBtn");
    const helpModal = document.getElementById("helpModal");
    const closeHelpBtn = document.getElementById("closeHelpBtn");
    
    // WebSocket connection
    let socket = io();
    
    // Socket event listeners
    socket.on('connect', function() {
        console.log('WebSocket connected');
        addNotification('System', 'Connected to real-time updates');
    });
    
    socket.on('disconnect', function() {
        console.log('WebSocket disconnected');
        addNotification('System', 'Disconnected from real-time updates', 'warning');
    });
    
    socket.on('queue_update', function(data) {
        console.log('Queue update received:', data);
        if (!queueContainer.classList.contains("hidden")) {
            updateQueueDisplay(data.queue);
        }
        liveCount.textContent = data.waiting_count;
        if (data.analytics) {
            document.getElementById('totalServed').textContent = data.analytics.total_served;
            document.getElementById('avgWaitTime').textContent = data.analytics.avg_wait_time;
        }
    });
    
    socket.on('notification', function(data) {
        console.log('Notification received:', data);
        Toastify({
            text: data.message,
            duration: 3000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: data.type === 'add' ? "#10B981" : "#EF4444",
            stopOnFocus: true
        }).showToast();
        addNotification(data.type === 'add' ? 'Added' : 'Removed', data.message);
    });
    
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
    
    // Dark Mode Setup
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
    
    // Insert a person
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
        });
    });
    
    // Delete the first person
    deleteBtn.addEventListener("click", function () {
        fetch('/delete', { method: 'POST' })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status !== 200) {
                alert(body.message);
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
        loadQueue();
    }
    
    function closeQueue() {
        queueContainer.classList.add("hidden");
    }
    
    // Fetch and update queue display
    function loadQueue() {
        fetch('/display')
        .then(response => response.json())
        .then(data => {
            updateQueueDisplay(data.queue);
        })
        .catch(error => console.error("Error loading queue:", error));
    }
    
    // Update queue display with priority badge (if applicable)
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
    
    // Export PDF functionality with enhanced logging and error handling
    const exportBtn = document.getElementById("exportBtn");
    if (exportBtn) {
        exportBtn.addEventListener("click", function() {
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
                    doc.setFontSize(20);
                    doc.text("QueueMaster Analytics Report", 105, 20, null, null, "center");
                    doc.setFontSize(12);
                    doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 105, 30, null, null, "center");
                    doc.setFontSize(14);
                    doc.text("Queue Performance Metrics:", 20, 50);
                    doc.setFontSize(12);
                    doc.text(`Total Customers Served: ${data.total_served}`, 30, 60);
                    doc.text(`Average Wait Time: ${data.avg_wait_time} seconds`, 30, 70);
                    doc.text(`Current Queue Length: ${liveCount.textContent} people`, 30, 80);
                    doc.save("QueueMaster-Analytics.pdf");
                })
                .catch(err => {
                    console.error("Error exporting PDF:", err);
                    alert("Export failed due to an error. Please check the console for details.");
                });
        });
    }
    
    // Help Modal functionality
    if (helpBtn && helpModal && closeHelpBtn) {
        helpBtn.addEventListener("click", function() {
            helpModal.classList.remove("hidden");
        });
        closeHelpBtn.addEventListener("click", function() {
            helpModal.classList.add("hidden");
        });
        // Close modal when clicking outside the modal content
        helpModal.addEventListener("click", function(e) {
            if (e.target === helpModal) {
                helpModal.classList.add("hidden");
            }
        });
    }
    
    // Initial load system message
    addNotification('System', 'Queue system initialized');
});
