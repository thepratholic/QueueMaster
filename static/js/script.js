document.addEventListener("DOMContentLoaded", function () {
    // DOM Element References
    const elements = {
        personInput: document.getElementById("personInput"),
        insertBtn: document.getElementById("insertBtn"),
        deleteBtn: document.getElementById("deleteBtn"),
        displayBtn: document.getElementById("displayBtn"),
        closeBtn: document.getElementById("closeBtn"),
        queueTableBody: document.querySelector("#queueTable tbody"),
        queueContainer: document.getElementById("queueContainer"),
        darkModeToggle: document.getElementById("darkModeToggle"),
        liveCount: document.getElementById("liveCount"),
        notificationsList: document.getElementById("notificationsList"),
        exportBtn: document.getElementById("exportBtn"),
        helpBtn: document.getElementById("helpBtn"),
        helpModal: document.getElementById("helpModal"),
        closeHelpBtn: document.getElementById("closeHelpBtn"),
        totalServed: document.getElementById("totalServed"),
        avgWaitTime: document.getElementById("avgWaitTime")
    };

    // Application State
    const appState = {
        refreshInterval: null,
        isQueueVisible: false,
        isDarkMode: localStorage.getItem("darkMode") === "enabled"
    };

    // --------------------------
    // Initialization
    // --------------------------
    function initializeApp() {
        setupDarkMode();
        setupEventListeners();
        startPeriodicRefresh();
        loadQueue();
        fetchAnalytics();
        addNotification('System', 'Queue system initialized');
    }

    // --------------------------
    // Notification System
    // --------------------------
    function addNotification(type, message, messageType = 'info') {
        const notificationItem = document.createElement('div');
        let typeClass;
        
        // Determine notification color based on type
        switch(type) {
            case 'Added':
                typeClass = 'text-green-600 dark:text-green-400';
                break;
            case 'Removed':
                typeClass = 'text-red-600 dark:text-red-400';
                break;
            case 'Warning':
                typeClass = 'text-yellow-600 dark:text-yellow-400';
                break;
            default:
                typeClass = 'text-blue-600 dark:text-blue-400';
        }

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        notificationItem.className = 'flex items-start';
        notificationItem.innerHTML = `
            <span class="inline-block w-16 text-xs text-gray-500 dark:text-gray-400">${timestamp}</span>
            <span class="font-medium ${typeClass} mr-1">${type}:</span>
            <span class="text-gray-700 dark:text-gray-300">${message}</span>
        `;
        
        elements.notificationsList.prepend(notificationItem);
        
        // Limit notifications to 20 to prevent overflow
        const items = elements.notificationsList.children;
        if (items.length > 20) {
            elements.notificationsList.removeChild(items[items.length - 1]);
        }
    }

    // --------------------------
    // Dark Mode Setup
    // --------------------------
    function setupDarkMode() {
        const rootElement = document.documentElement;
        
        if (appState.isDarkMode) {
            rootElement.classList.add("dark");
            elements.darkModeToggle.checked = true;
        } else {
            rootElement.classList.remove("dark");
            elements.darkModeToggle.checked = false;
        }
    }

    function toggleDarkMode() {
        const rootElement = document.documentElement;
        appState.isDarkMode = elements.darkModeToggle.checked;
        
        if (appState.isDarkMode) {
            rootElement.classList.add("dark");
            localStorage.setItem("darkMode", "enabled");
        } else {
            rootElement.classList.remove("dark");
            localStorage.setItem("darkMode", "disabled");
        }
    }

    // --------------------------
    // Data Fetching Functions
    // --------------------------
    function loadQueue() {
        fetch('/display')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                updateQueueDisplay(data.queue);
                elements.liveCount.textContent = data.queue.length;
            })
            .catch(error => {
                console.error("Error loading queue:", error);
                addNotification('Warning', 'Failed to load queue data', 'warning');
            });
    }

    function fetchAnalytics() {
        fetch('/analytics')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                elements.totalServed.textContent = data.total_served;
                elements.avgWaitTime.textContent = data.avg_wait_time;
            })
            .catch(error => {
                console.error("Error fetching analytics:", error);
                addNotification('Warning', 'Failed to load analytics data', 'warning');
            });
    }

    function startPeriodicRefresh() {
        // Refresh data every 30 seconds
        appState.refreshInterval = setInterval(() => {
            loadQueue();
            fetchAnalytics();
        }, 30000);
    }

    // --------------------------
    // Queue Display Functions
    // --------------------------
    function updateQueueDisplay(queueData) {
        elements.queueTableBody.innerHTML = "";
        
        if (!queueData || queueData.length === 0) {
            const emptyRow = document.createElement("tr");
            emptyRow.className = "bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100";
            
            const emptyCell = document.createElement("td");
            emptyCell.textContent = "Queue is empty";
            emptyCell.className = "p-2 border text-center";
            emptyCell.colSpan = 2;
            
            emptyRow.appendChild(emptyCell);
            elements.queueTableBody.appendChild(emptyRow);
            return;
        }

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

            // Add priority badge if priority is not normal
            if (entry.priority && entry.priority.toLowerCase() !== "normal") {
                let badge = document.createElement("span");
                badge.className = "ml-2 inline-block text-xs px-2 py-1 rounded";
                
                switch (entry.priority.toLowerCase()) {
                    case "urgent":
                        badge.classList.add("bg-red-500", "text-white");
                        badge.textContent = "Urgent";
                        break;
                    case "low":
                        badge.classList.add("bg-blue-500", "text-white");
                        badge.textContent = "Low";
                        break;
                    default:
                        badge.classList.add("bg-gray-500", "text-white");
                        badge.textContent = entry.priority;
                }
                
                nameCell.appendChild(badge);
            }

            // Add category badge if category is not general
            if (entry.category && entry.category.toLowerCase() !== "general") {
                let categoryBadge = document.createElement("span");
                categoryBadge.className = "ml-2 inline-block text-xs px-2 py-1 rounded bg-purple-500 text-white";
                categoryBadge.textContent = entry.category;
                nameCell.appendChild(categoryBadge);
            }

            row.appendChild(indexCell);
            row.appendChild(nameCell);
            elements.queueTableBody.appendChild(row);
        });
    }

    function showQueue() {
        elements.queueContainer.classList.remove("hidden");
        appState.isQueueVisible = true;
        loadQueue();
    }

    function closeQueue() {
        elements.queueContainer.classList.add("hidden");
        appState.isQueueVisible = false;
    }

    // --------------------------
    // Event Handlers
    // --------------------------
    function handleInsert() {
        let personName = elements.personInput.value.trim();
        
        if (!personName) {
            showToast("Please enter a valid name.", "error");
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
                showToast(body.message, "error");
            } else {
                showToast(`${personName} has been inserted into the queue`, "success");
                addNotification('Added', `${personName} has been inserted into the queue`);
                loadQueue();
                fetchAnalytics();
            }
            elements.personInput.value = "";
        })
        .catch(error => {
            console.error("Error inserting person:", error);
            showToast("Failed to insert person into queue", "error");
        });
    }

    function handleDelete() {
        fetch('/delete', { method: 'POST' })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status !== 200) {
                showToast(body.message, "error");
            } else {
                showToast(body.message, "info");
                addNotification('Removed', body.message);
                loadQueue();
                fetchAnalytics();
            }
        })
        .catch(error => {
            console.error("Error deleting person:", error);
            showToast("Failed to remove person from queue", "error");
        });
    }

    function handleExportPDF() {
        fetch('/analytics')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!window.jspdf || !window.jspdf.jsPDF) {
                console.error("jsPDF library is not loaded");
                showToast("Export failed: jsPDF library is not available.", "error");
                return;
            }
            
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            const pageHeight = doc.internal.pageSize.height;
            
            // Title and Header
            doc.setFontSize(20);
            doc.text("QueueMaster Analytics Report", 105, 20, null, null, "center");
            
            // Date and Time
            doc.setFontSize(12);
            const now = new Date();
            doc.text(`Generated on: ${now.toLocaleDateString()} at ${now.toLocaleTimeString()}`, 105, 30, null, null, "center");
            
            // Basic Stats
            doc.setFontSize(14);
            doc.text("Queue Performance Metrics:", 20, 50);
            doc.setFontSize(12);
            doc.text(`Total Customers Served: ${data.total_served}`, 30, 60);
            doc.text(`Average Wait Time: ${data.avg_wait_time} seconds`, 30, 70);
            doc.text(`Current Queue Length: ${elements.liveCount.textContent} people`, 30, 80);
            
            // Served Customers List
            let yPos = 100;
            doc.setFontSize(14);
            doc.text("Served Customers:", 20, yPos);
            yPos += 10;
            
            if (data.served_details && data.served_details.length > 0) {
                // Table Header
                doc.setFontSize(11);
                doc.setFont(undefined, 'bold');
                doc.text("No.", 20, yPos);
                doc.text("Name", 40, yPos);
                doc.text("Inserted At", 100, yPos);
                doc.text("Served At", 160, yPos);
                yPos += 8;
                doc.setFont(undefined, 'normal');
                
                // Draw line under header
                doc.line(20, yPos - 4, 190, yPos - 4);
                
                data.served_details.forEach((customer, index) => {
                    // Check if we need a new page
                    if (yPos >= pageHeight - 20) {
                        doc.addPage();
                        yPos = 20;
                        
                        // Add header to new page
                        doc.setFontSize(11);
                        doc.setFont(undefined, 'bold');
                        doc.text("No.", 20, yPos);
                        doc.text("Name", 40, yPos);
                        doc.text("Inserted At", 100, yPos);
                        doc.text("Served At", 160, yPos);
                        yPos += 8;
                        doc.setFont(undefined, 'normal');
                        
                        // Draw line under header
                        doc.line(20, yPos - 4, 190, yPos - 4);
                    }
                    
                    // Format dates for better readability
                    let arrivalDate = "N/A";
                    let servedDate = "N/A";
                    
                    if (customer.arrival_time && customer.arrival_time !== "N/A") {
                        const arrival = new Date(customer.arrival_time);
                        arrivalDate = `${arrival.toLocaleDateString()} ${arrival.toLocaleTimeString()}`;
                    }
                    
                    if (customer.served_time && customer.served_time !== "N/A") {
                        const served = new Date(customer.served_time);
                        servedDate = `${served.toLocaleDateString()} ${served.toLocaleTimeString()}`;
                    }
                    
                    doc.text(`${index + 1}.`, 20, yPos);
                    doc.text(customer.person_name || "Unknown", 40, yPos);
                    doc.text(arrivalDate, 100, yPos);
                    doc.text(servedDate, 160, yPos);
                    
                    yPos += 8;
                });
            } else {
                doc.setFontSize(12);
                doc.text("No served entries found yet.", 30, yPos);
            }
            
            // Footer
            const pageCount = doc.internal.getNumberOfPages();
            for (let i = 1; i <= pageCount; i++) {
                doc.setPage(i);
                doc.setFontSize(10);
                doc.text(`Page ${i} of ${pageCount}`, 105, doc.internal.pageSize.height - 10, null, null, "center");
                doc.text("QueueMaster - Generated Report", 20, doc.internal.pageSize.height - 10);
            }
            
            doc.save("QueueMaster-Analytics.pdf");
            showToast("PDF exported successfully!", "success");
        })
        .catch(error => {
            console.error("Error exporting PDF:", error);
            showToast("Export failed. Please try again later.", "error");
        });
    }

    function handleHelpOpen() {
        elements.helpModal.classList.remove("hidden");
    }

    function handleHelpClose() {
        elements.helpModal.classList.add("hidden");
    }

    // --------------------------
    // Utility Functions
    // --------------------------
    function showToast(message, type = "info") {
        let backgroundColor;
        
        switch (type) {
            case "success":
                backgroundColor = "#10B981"; // Green
                break;
            case "error":
                backgroundColor = "#EF4444"; // Red
                break;
            case "warning":
                backgroundColor = "#F59E0B"; // Amber
                break;
            default:
                backgroundColor = "#3B82F6"; // Blue
        }
        
        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor: backgroundColor,
            stopOnFocus: true
        }).showToast();
    }

    // --------------------------
    // Event Listeners Setup
    // --------------------------
    function setupEventListeners() {
        // Dark mode toggle
        elements.darkModeToggle.addEventListener("change", toggleDarkMode);
        
        // Queue management
        elements.insertBtn.addEventListener("click", handleInsert);
        elements.deleteBtn.addEventListener("click", handleDelete);
        elements.displayBtn.addEventListener("click", showQueue);
        elements.closeBtn.addEventListener("click", closeQueue);
        
        // Enter key for person input
        elements.personInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                handleInsert();
            }
        });
        
        // Help modal
        if (elements.helpBtn && elements.helpModal && elements.closeHelpBtn) {
            elements.helpBtn.addEventListener("click", handleHelpOpen);
            elements.closeHelpBtn.addEventListener("click", handleHelpClose);
            
            // Close modal when clicking outside
            elements.helpModal.addEventListener("click", function(event) {
                if (event.target === elements.helpModal) {
                    handleHelpClose();
                }
            });
        }
        
        // Export PDF
        if (elements.exportBtn) {
            elements.exportBtn.addEventListener("click", handleExportPDF);
        }
    }

    // Initialize the application
    initializeApp();
});