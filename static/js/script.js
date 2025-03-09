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
    
    // Advanced controls
    const pauseBtn = document.getElementById("pauseBtn");
    const resumeBtn = document.getElementById("resumeBtn");
    const setPriorityBtn = document.getElementById("setPriorityBtn");
    const setCategoryBtn = document.getElementById("setCategoryBtn");
    const advPersonNameInput = document.getElementById("advPersonName");
    const prioritySelect = document.getElementById("prioritySelect");
    const catPersonNameInput = document.getElementById("catPersonName");
    const categoryInput = document.getElementById("categoryInput");
    
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
    
    function updateQueueDisplay(queueData) {
        queueTableBody.innerHTML = "";
        queueData.forEach((entry, index) => {
            let row = document.createElement("tr");
            row.className = "bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100";
            let indexCell = document.createElement("td");
            indexCell.textContent = index + 1;
            indexCell.className = "p-2 border";
            let nameCell = document.createElement("td");
            nameCell.textContent = entry.person_name;
            nameCell.className = "p-2 border";
            row.appendChild(indexCell);
            row.appendChild(nameCell);
            queueTableBody.appendChild(row);
        });
        enableDragAndDropForQueue();
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
                });
        });
    }
    
    // Advanced Features
    
    // Toggle Pause/Resume
    if(pauseBtn) {
        pauseBtn.addEventListener("click", function() {
            fetch('/api/pause_queue', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ pause: true })
            })
            .then(res => res.json())
            .then(data => {
                Toastify({
                    text: data.message,
                    duration: 3000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#f59e0b"
                }).showToast();
            })
            .catch(err => console.error("Error pausing queue:", err));
        });
    }
    
    if(resumeBtn) {
        resumeBtn.addEventListener("click", function() {
            fetch('/api/pause_queue', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ pause: false })
            })
            .then(res => res.json())
            .then(data => {
                Toastify({
                    text: data.message,
                    duration: 3000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#10B981"
                }).showToast();
            })
            .catch(err => console.error("Error resuming queue:", err));
        });
    }
    
    // Set Priority for a specific person
    if(setPriorityBtn) {
        setPriorityBtn.addEventListener("click", function() {
            const personName = advPersonNameInput.value.trim();
            const newPriority = prioritySelect.value;
            if(!personName) {
                alert("Please enter a person name for setting priority.");
                return;
            }
            fetch('/api/set_priority', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: personName, priority: newPriority })
            })
            .then(res => res.json())
            .then(data => {
                if(data.error) alert(data.error);
                else Toastify({
                    text: data.message,
                    duration: 3000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#3b82f6"
                }).showToast();
            })
            .catch(err => console.error("Error setting priority:", err));
        });
    }
    
    // Set Category for a specific person
    if(setCategoryBtn) {
        setCategoryBtn.addEventListener("click", function() {
            const personName = catPersonNameInput.value.trim();
            const category = categoryInput.value.trim();
            if(!personName || !category) {
                alert("Please enter both person name and category.");
                return;
            }
            fetch('/api/set_category', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name: personName, category: category })
            })
            .then(res => res.json())
            .then(data => {
                if(data.error) alert(data.error);
                else Toastify({
                    text: data.message,
                    duration: 3000,
                    gravity: "top",
                    position: "right",
                    backgroundColor: "#6366f1"
                }).showToast();
            })
            .catch(err => console.error("Error setting category:", err));
        });
    }
    
    // Enable drag and drop reordering for the queue table
    function enableDragAndDropForQueue() {
        const tableBody = document.querySelector("#queueTable tbody");
        if (!tableBody) return;
        let dragSrcEl = null;
    
        function handleDragStart(e) {
            dragSrcEl = this;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', this.innerHTML);
        }
    
        function handleDragOver(e) {
            if (e.preventDefault) e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            return false;
        }
    
        function handleDrop(e) {
            if (e.stopPropagation) e.stopPropagation();
            if (dragSrcEl !== this) {
                dragSrcEl.innerHTML = this.innerHTML;
                this.innerHTML = e.dataTransfer.getData('text/html');
                const newOrder = [];
                tableBody.querySelectorAll('tr').forEach(row => {
                    const nameCell = row.cells[1];
                    if (nameCell) newOrder.push(nameCell.textContent.trim());
                });
                fetch('/api/reorder_queue', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ new_order: newOrder })
                })
                .then(res => res.json())
                .then(data => {
                    Toastify({
                        text: data.message,
                        duration: 3000,
                        gravity: "top",
                        position: "right",
                        backgroundColor: "#6366f1"
                    }).showToast();
                })
                .catch(err => console.error("Error reordering queue:", err));
            }
            return false;
        }
    
        tableBody.querySelectorAll('tr').forEach(row => {
            row.setAttribute('draggable', true);
            row.addEventListener('dragstart', handleDragStart, false);
            row.addEventListener('dragover', handleDragOver, false);
            row.addEventListener('drop', handleDrop, false);
        });
    }
    
    // Initial load system message
    addNotification('System', 'Queue system initialized');
});
