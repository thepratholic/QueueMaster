// 

document.addEventListener("DOMContentLoaded", function () {
    const personInput = document.getElementById("personInput");
    const insertBtn = document.getElementById("insertBtn");
    const deleteBtn = document.getElementById("deleteBtn");
    const displayBtn = document.getElementById("displayBtn");
    const queueList = document.getElementById("queueList");
    const queueContainer = document.getElementById("queueContainer");
    const toggleSwitch = document.getElementById("darkModeToggle");
    const body = document.body;

    // Dark Mode Setup
    if (localStorage.getItem("darkMode") === "enabled") {
        body.classList.add("dark-mode");
        toggleSwitch.checked = true;
    }

    toggleSwitch.addEventListener("change", function () {
        if (this.checked) {
            body.classList.add("dark-mode");
            localStorage.setItem("darkMode", "enabled");
        } else {
            body.classList.remove("dark-mode");
            localStorage.setItem("darkMode", "disabled");
        }
    });

    // Insert a person into the queue
    insertBtn.addEventListener("click", function () {
        let personName = personInput.value.trim();
        
        if (personName === "") {
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
            if (status === 400) {
                alert(body.message); // Show alert only when queue is full
            }
            personInput.value = "";
            updateQueue();  // Refresh queue display
            updateAnalytics(); // Update analytics
        });
    });

    // Delete the first person from the queue
    deleteBtn.addEventListener("click", function () {
        fetch('/delete', { method: 'POST' })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 400) {
                alert(body.message); // Show alert only when queue is empty
            }
            updateQueue();  // Refresh queue display
            updateAnalytics(); // Update analytics
        });
    });

    // Display the queue
    displayBtn.addEventListener("click", function () {
        updateQueue();
    });

    function updateQueue() {
        fetch('/display')
            .then(response => response.json())
            .then(data => {
                queueList.innerHTML = "";
                data.queue.forEach((person, index) => {
                    let li = document.createElement("li");
                    li.textContent = `${index + 1}. ${person}`; // Correctly format index
                    li.style.listStyle = "none";
                    queueList.appendChild(li);
                });
                queueContainer.classList.remove("hidden");
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

    // Load initial queue data
    updateQueue();
    updateAnalytics();

    document.getElementById("exportBtn").addEventListener("click", function () {
        fetch('/display')
            .then(response => response.json())
            .then(data => {
                if (data.queue.length === 0) {
                    alert("Queue is empty! No data to export.");
                    return;
                }

                // Use jsPDF to create an elegant PDF
                const { jsPDF } = window.jspdf;
                let doc = new jsPDF();

                // Premium Styling
                doc.setFont("helvetica", "bold");
                doc.setFontSize(22);
                doc.setTextColor(30, 57, 114);
                doc.text("Queue Data Report", 14, 20);

                doc.setFontSize(12);
                doc.setTextColor(50, 50, 50);
                doc.text("Generated on: " + new Date().toLocaleString(), 14, 30);

                let yPos = 50;
                data.queue.forEach((person, index) => {
                    doc.setFontSize(14);
                    doc.setTextColor(20, 20, 20);
                    doc.text(`${index + 1}. ${person}`, 14, yPos);
                    yPos += 10;
                });

                // Smooth save animation
                setTimeout(() => {
                    doc.save("Queue_Data.pdf");
                }, 500);
            });
    });
});