document.getElementById('insertBtn').addEventListener('click', () => {
    const person = document.getElementById('personInput').value;
    if (person) {
        fetch('/insert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({ 'element': person })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            document.getElementById('personInput').value = '';  // Clear input field after insertion
            updateAnalytics();  // Update analytics after insertion
        });
    } else {
        alert("Please enter a name before inserting.");
    }
});

document.getElementById('deleteBtn').addEventListener('click', () => {
    fetch('/delete', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        updateAnalytics();  // Update analytics after deletion
    });
});

document.getElementById('displayBtn').addEventListener('click', () => {
    updateQueue();
});

function updateQueue() {
    fetch('/display')
        .then(response => response.json())
        .then(data => {
            const queueList = document.getElementById('queueList');
            queueList.innerHTML = '';
            data.queue.forEach(person => {
                const listItem = document.createElement('li');
                listItem.textContent = person;
                queueList.appendChild(listItem);
            });
            document.getElementById('queueContainer').classList.remove('hidden');
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
