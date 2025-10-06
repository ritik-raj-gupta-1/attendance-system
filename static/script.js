const API_BASE = window.location.origin;

function showAlert(message, type = 'error') {
    const alertBox = document.getElementById('alert-box');
    alertBox.textContent = message;
    alertBox.className = `alert ${type}`;
    alertBox.style.display = 'block';
    setTimeout(() => { alertBox.style.display = 'none'; }, 4000);
}

function getDeviceId() {
    let deviceId = localStorage.getItem('deviceId');
    if (!deviceId) {
        deviceId = crypto.randomUUID();
        localStorage.setItem('deviceId', deviceId);
    }
    return deviceId;
}

function toggleForms() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
    registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
}

async function handleStudentLogin(event) {
    event.preventDefault();
    const identifier = document.getElementById('login-identifier').value;
    const password = document.getElementById('login-password').value;
    try {
        const response = await fetch(`${API_BASE}/api/student_login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier, password }),
        });
        const data = await response.json();
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            showAlert(data.message || 'Login failed.');
        }
    } catch (error) {
        showAlert('Could not connect to the server.');
    }
}

async function handleAdminLogin(event) {
    event.preventDefault();
    const identifier = document.getElementById('admin-identifier').value;
    const password = document.getElementById('admin-password').value;
    try {
        const response = await fetch(`${API_BASE}/api/admin_login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier, password }),
        });
        const data = await response.json();
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            showAlert(data.message || 'Login failed.');
        }
    } catch (error) {
        showAlert('Could not connect to the server.');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const enrollment_number = document.getElementById('register-enrollment').value;
    const password = document.getElementById('register-password').value;
    const device_id = getDeviceId();
    try {
        const response = await fetch(`${API_BASE}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enrollment_number, password, device_id }),
        });
        const data = await response.json();
        if (data.success) {
            showAlert('Registration successful! You can now log in.', 'success');
            toggleForms();
        } else {
            showAlert(data.message || 'Registration failed.');
        }
    } catch (error) {
        showAlert('Could not connect to the server.');
    }
}

let countdownInterval;

function startCountdown(remainingSeconds) {
    const timerElement = document.getElementById('session-timer');
    if (!timerElement) return;

    if (countdownInterval) clearInterval(countdownInterval);

    let duration = Math.round(remainingSeconds);

    countdownInterval = setInterval(() => {
        if (duration <= 0) {
            clearInterval(countdownInterval);
            timerElement.innerHTML = "Session Ended";
            checkSessionStatus();
            return;
        }
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        timerElement.innerHTML = `Time Left: ${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        duration--;
    }, 1000);
}

function stopCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);
    const timerElement = document.getElementById('session-timer');
    if (timerElement) timerElement.innerHTML = "";
}

async function checkSessionStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/get_active_session`);
        if (!response.ok) return;
        
        const data = await response.json();
        
        const markBtn = document.getElementById('mark-attendance-btn');
        if (markBtn) {
            markBtn.disabled = !data.is_active;
            markBtn.textContent = data.is_active ? 'Mark My Attendance' : 'Session is not active';
        }
        
        const startBtn = document.getElementById('start-session-btn');
        const endBtn = document.getElementById('end-session-btn');
        if (startBtn && endBtn) {
            startBtn.style.display = data.is_active ? 'none' : 'inline-block';
            endBtn.style.display = data.is_active ? 'inline-block' : 'none';
        }

        if (data.is_active && data.remaining_seconds > 0) {
            startCountdown(data.remaining_seconds);
        } else {
            stopCountdown();
        }
    } catch (error) {
        console.error("Error checking session status:", error);
    }
}

// --- Admin Dashboard ---

function initAdminDashboard() {
    checkSessionStatus();
    fetchTodayAttendance();
    fetchRequests();
    setInterval(checkSessionStatus, 5000);
    setInterval(fetchTodayAttendance, 30000); // Refresh attendance list
    setInterval(fetchRequests, 60000); // Refresh requests list
}

async function startAttendanceSession() {
    const startButton = document.getElementById('start-session-btn');
    startButton.disabled = true;
    startButton.textContent = 'Getting location...';

    if (!navigator.geolocation) {
        showAlert('Geolocation is not supported by your browser.');
        startButton.disabled = false;
        startButton.textContent = 'Start 5-Min Attendance Session';
        return;
    }
    navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        try {
            const response = await fetch(`${API_BASE}/api/admin/start_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: latitude, lon: longitude }),
            });
            const data = await response.json();
            showAlert(data.message, data.success ? 'success' : 'error');
            await checkSessionStatus();
            await fetchTodayAttendance();
        } catch(e) {
            showAlert('Server error while starting session.');
        } finally {
            startButton.disabled = false;
            startButton.textContent = 'Start 5-Min Attendance Session';
        }
    }, () => {
        showAlert('Could not get location. Please grant permission.');
        startButton.disabled = false;
        startButton.textContent = 'Start 5-Min Attendance Session';
    });
}

async function endAttendanceSession() {
    const endButton = document.getElementById('end-session-btn');
    endButton.disabled = true;
    try {
        const response = await fetch(`${API_BASE}/api/admin/end_session`, { method: 'POST' });
        const data = await response.json();
        showAlert(data.message, data.success ? 'success' : 'error');
        await checkSessionStatus();
    } catch(e) {
        showAlert('Server error while ending session.');
    } finally {
        endButton.disabled = false;
    }
}

async function fetchTodayAttendance() {
    const listDiv = document.getElementById('today-attendance-list');
    
    try {
        const response = await fetch(`${API_BASE}/api/admin/get_today_attendance`);
        if (!response.ok) {
            listDiv.innerHTML = '<p class="loading-text">Could not load data. Unauthorized or server error.</p>';
            return;
        }

        const data = await response.json();
        
        if (!Array.isArray(data)) {
            listDiv.innerHTML = '<p class="loading-text">Received invalid data from server.</p>';
            return;
        }

        if (data.length === 0) {
            listDiv.innerHTML = '<p class="loading-text">No session has been started for today.</p>';
            return;
        }

        listDiv.innerHTML = ''; 
        data.forEach(student => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'list-item';
            itemDiv.innerHTML = `
                <span class="student-info">${student.name} (${student.enrollment_number})</span>
                <span class="status-toggle ${student.status}" onclick="toggleStatus(${student.record_id}, '${student.status}')">
                    ${student.status}
                </span>
            `;
            listDiv.appendChild(itemDiv);
        });
        // After rendering, re-apply search filter if any
        searchStudents();
    } catch (error) {
        listDiv.innerHTML = '<p class="loading-text">Error fetching attendance. Please check connection.</p>';
        console.error("Error fetching attendance:", error);
    }
}


async function toggleStatus(record_id, current_status) {
    const new_status = current_status === 'Present' ? 'Absent' : 'Present';
    try {
        await fetch(`${API_BASE}/api/admin/update_attendance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ record_id, status: new_status }),
        });
        await fetchTodayAttendance();
    } catch(e) {
        showAlert('Failed to update status.');
    }
}

async function fetchRequests() {
    const listDiv = document.getElementById('requests-list');
    try {
        const response = await fetch(`${API_BASE}/api/admin/get_requests`);
        if (!response.ok) {
            listDiv.innerHTML = '<p>Could not load requests.</p>';
            return;
        }
        const data = await response.json();
        if (!Array.isArray(data)) {
            listDiv.innerHTML = '<p>Received invalid data.</p>';
            return;
        }

        if (data.length === 0) {
            listDiv.innerHTML = '<p>No pending requests.</p>';
            return;
        }
        listDiv.innerHTML = data.map(req => `
            <div class="list-item">
                <span>${req.name} (${req.enrollment_number})</span>
                <button onclick="approveRequest(${req.id})">Approve</button>
            </div>
        `).join('');
    } catch(e) {
        listDiv.innerHTML = '<p>Error loading requests.</p>';
    }
}

async function approveRequest(request_id) {
    try {
        const response = await fetch(`${API_BASE}/api/admin/approve_request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id }),
        });
        const data = await response.json();
        showAlert(data.message, data.success ? 'success' : 'error');
        await fetchRequests();
    } catch(e) {
        showAlert('Failed to approve request.');
    }
}

function searchStudents() {
    const input = document.getElementById('student-search');
    const filter = input.value.toUpperCase();
    const list = document.getElementById('today-attendance-list');
    const items = list.getElementsByClassName('list-item');

    for (let i = 0; i < items.length; i++) {
        const studentInfo = items[i].getElementsByClassName("student-info")[0];
        if (studentInfo) {
            const txtValue = studentInfo.textContent || studentInfo.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                items[i].style.display = "flex";
            } else {
                items[i].style.display = "none";
            }
        }
    }
}

// --- Student Dashboard ---

function initStudentDashboard() {
    checkSessionStatus();
    updateStudentStats();
    setInterval(checkSessionStatus, 5000);
    setInterval(updateStudentStats, 30000);
}

async function updateStudentStats() {
    try {
        const response = await fetch(`${API_BASE}/api/student/get_status`);
        if (!response.ok) return;

        const data = await response.json();

        document.getElementById('days-present').textContent = data.days_present || 0;
        document.getElementById('total-working-days').textContent = data.total_working_days || 0;
        const percentage = data.total_working_days > 0 ? ((data.days_present / data.total_working_days) * 100).toFixed(2) : 0;
        document.getElementById('percentage').textContent = `${percentage}%`;
        
        const presentList = document.getElementById('present-list-today');
        if (data.present_list_today && data.present_list_today.length > 0) {
            presentList.innerHTML = data.present_list_today.map(name => `<li>${name}</li>`).join('');
        } else {
            presentList.innerHTML = '<li>No one marked present yet.</li>';
        }
    } catch(e) {
        console.error("Error updating student stats:", e);
    }
}

function markAttendance() {
    const markBtn = document.getElementById('mark-attendance-btn');
    markBtn.disabled = true;
    markBtn.textContent = 'Getting Location...';
    if (!navigator.geolocation) {
        showAlert('Geolocation is not supported by your browser.');
        markBtn.disabled = false;
        markBtn.textContent = 'Mark My Attendance';
        return;
    }
    navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        const device_id = getDeviceId();
        try {
            const response = await fetch(`${API_BASE}/api/student/mark_attendance`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: latitude, lon: longitude, device_id }),
            });
            const data = await response.json();
            showAlert(data.message, data.success ? 'success' : 'error');
            if (data.success) {
                markBtn.textContent = 'Marked!';
                await updateStudentStats();
            } else {
                markBtn.disabled = false;
                markBtn.textContent = 'Mark My Attendance';
            }
        } catch(e) {
            showAlert('Server error while marking attendance.');
            markBtn.disabled = false;
            markBtn.textContent = 'Mark My Attendance';
        }
    }, () => {
        showAlert('Could not get location. Please grant permission.');
        markBtn.disabled = false;
        markBtn.textContent = 'Mark My Attendance';
    });
}

async function requestReRegistration() {
    if (confirm('Are you sure you want to request a device change? This will allow you to register a new device.')) {
        try {
            const response = await fetch(`${API_BASE}/api/student/request_reregistration`, { method: 'POST' });
            const data = await response.json();
            showAlert(data.message, data.success ? 'success' : 'error');
        } catch(e) {
            showAlert('Could not send request.');
        }
    }
}