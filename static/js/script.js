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
    
    // Listen for queue updates
    socket.on('queue_update', function(data) {
        console.log('Queue update received:', data);
        
        // Update queue display if visible
        if (!queueContainer.classList.contains("hidden")) {
            updateQueueDisplay(data.queue);
        }
        
        // Update live count
        liveCount.textContent = data.waiting_count;
        
        // Update analytics
        if (data.analytics) {
            document.getElementById('totalServed').textContent = data.analytics.total_served;
            document.getElementById('avgWaitTime').textContent = data.analytics.avg_wait_time;
        }
    });
    
    // Listen for notifications
    socket.on('notification', function(data) {
        console.log('Notification received:', data);
        
        // Display toast notification
        Toastify({
            text: data.message,
            duration: 3000,
            close: true,
            gravity: "top",
            position: "right",
            backgroundColor: data.type === 'add' ? "#10B981" : "#EF4444",
            stopOnFocus: true
        }).showToast();
        
        // Add to notifications list
        addNotification(data.type === 'add' ? 'Added' : 'Removed', data.message);
    });
    
    // Function to add notification to the list
    function addNotification(type, message, messageType = 'info') {
        const notificationItem = document.createElement('div');
        
        // Define classes based on message type
        let typeClass = 'text-blue-600 dark:text-blue-400';
        if (messageType === 'warning') {
            typeClass = 'text-yellow-600 dark:text-yellow-400';
        } else if (type === 'Added') {
            typeClass = 'text-green-600 dark:text-green-400';
        } else if (type === 'Removed') {
            typeClass = 'text-red-600 dark:text-red-400';
        }
        
        // Add timestamp
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        notificationItem.className = 'flex items-start';
        notificationItem.innerHTML = `
            <span class="inline-block w-16 text-xs text-gray-500 dark:text-gray-400">${timestamp}</span>
            <span class="font-medium ${typeClass} mr-1">${type}:</span>
            <span class="text-gray-700 dark:text-gray-300">${message}</span>
        `;
        
        notificationsList.prepend(notificationItem);
        
        // Limit to last 20 notifications
        const items = notificationsList.children;
        if (items.length > 20) {
            notificationsList.removeChild(items[items.length - 1]);
        }
    }
    
    // For Tailwind dark mode, toggle the 'dark' class on the <html> element.
    const rootElement = document.documentElement;

    // Dark Mode Setup: check localStorage and update the root element accordingly.
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
            // No manual update needed; WebSocket handles it
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
            // No manual update needed; WebSocket handles it
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

    // **FIX**: Instead of `socket.emit('get_queue')`, directly load the queue
    function showQueue() {
        queueContainer.classList.remove("hidden");
        loadQueue();
    }

    function closeQueue() {
        queueContainer.classList.add("hidden");
    }

    // Manually fetch the queue and update display
    function loadQueue() {
        fetch('/display')
        .then(response => response.json())
        .then(data => {
            updateQueueDisplay(data.queue);
        })
        .catch(error => console.error("Error loading queue:", error));
    }

    // Update queue display with data
    function updateQueueDisplay(queueData) {
        queueTableBody.innerHTML = "";
        queueData.forEach((person, index) => {
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
    }

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
                    // We can also show the live queue count from the page:
                    doc.text(`Current Queue Length: ${liveCount.textContent} people`, 30, 80);
                    
                    // Save PDF
                    doc.save("QueueMaster-Analytics.pdf");
                });
        });
    }

    // Initial load system message
    addNotification('System', 'Queue system initialized');
});
