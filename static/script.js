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
}

async function handleAdminLogin(event) {
    event.preventDefault();
    const identifier = document.getElementById('admin-identifier').value;
    const password = document.getElementById('admin-password').value;
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
}

async function handleRegister(event) {
    event.preventDefault();
    const enrollment_number = document.getElementById('register-enrollment').value;
    const password = document.getElementById('register-password').value;
    const device_id = getDeviceId();
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
}

let countdownInterval;

function startCountdown(endTime) {
    const timerElement = document.getElementById('session-timer');
    if (!timerElement) return;

    if (countdownInterval) clearInterval(countdownInterval);

    const end = new Date(endTime.replace(' ', 'T')).getTime();

    countdownInterval = setInterval(() => {
        const now = new Date().getTime();
        const distance = end - now;

        if (distance < 0) {
            clearInterval(countdownInterval);
            timerElement.innerHTML = "Session Ended";
            checkSessionStatus();
            return;
        }
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        timerElement.innerHTML = `Time Left: ${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
}

function stopCountdown() {
    if (countdownInterval) clearInterval(countdownInterval);
    const timerElement = document.getElementById('session-timer');
    if (timerElement) timerElement.innerHTML = "";
}

async function checkSessionStatus() {
    const response = await fetch(`${API_BASE}/api/get_active_session`);
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

    if (data.is_active) {
        startCountdown(data.end_time);
    } else {
        stopCountdown();
    }
}

function initAdminDashboard() {
    checkSessionStatus();
    fetchTodayAttendance();
    fetchRequests();
    setInterval(checkSessionStatus, 5000);
}

async function startAttendanceSession() {
    const startButton = document.getElementById('start-session-btn');
    startButton.disabled = true;
    startButton.textContent = 'Getting location...';
    if (!navigator.geolocation) {
        showAlert('Geolocation is not supported by your browser.');
        startButton.disabled = false; return;
    }
    navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        const response = await fetch(`${API_BASE}/api/admin/start_session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: latitude, lon: longitude }),
        });
        const data = await response.json();
        showAlert(data.message, data.success ? 'success' : 'error');
        checkSessionStatus();
        fetchTodayAttendance();
        startButton.textContent = 'Start 5-Min Attendance Session';
    }, () => {
        showAlert('Could not get location. Please grant permission and ensure location services are enabled.');
        startButton.disabled = false;
        startButton.textContent = 'Start 5-Min Attendance Session';
    });
}

async function endAttendanceSession() {
    const endButton = document.getElementById('end-session-btn');
    endButton.disabled = true;
    const response = await fetch(`${API_BASE}/api/admin/end_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
    });
    const data = await response.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    checkSessionStatus();
    endButton.disabled = false;
}

async function fetchTodayAttendance() {
    const response = await fetch(`${API_BASE}/api/admin/get_today_attendance`);
    const data = await response.json();
    const listDiv = document.getElementById('today-attendance-list');
    if (data.length === 0) {
        listDiv.innerHTML = '<p>No session started for today.</p>';
        return;
    }
    listDiv.innerHTML = data.map(student => `
        <div class="list-item">
            <span>${student.name} (${student.enrollment_number})</span>
            <span class="status-toggle ${student.status}" onclick="toggleStatus(${student.record_id}, '${student.status}')">
                ${student.status}
            </span>
        </div>
    `).join('');
}

async function toggleStatus(record_id, current_status) {
    const new_status = current_status === 'Present' ? 'Absent' : 'Present';
    await fetch(`${API_BASE}/api/admin/update_attendance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ record_id, status: new_status }),
    });
    fetchTodayAttendance();
}

async function fetchRequests() {
    const response = await fetch(`${API_BASE}/api/admin/get_requests`);
    const data = await response.json();
    const listDiv = document.getElementById('requests-list');
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
}

async function approveRequest(request_id) {
    await fetch(`${API_BASE}/api/admin/approve_request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id }),
    });
    showAlert('Request approved. Student can register a new device.', 'success');
    fetchRequests();
}

function initStudentDashboard() {
    checkSessionStatus();
    updateStudentStats();
    setInterval(checkSessionStatus, 5000);
    setInterval(updateStudentStats, 30000);
}

async function updateStudentStats() {
    const response = await fetch(`${API_BASE}/api/student/get_status`);
    const data = await response.json();
    document.getElementById('days-present').textContent = data.days_present;
    document.getElementById('total-sessions').textContent = data.total_sessions;
    const percentage = data.total_sessions > 0 ? ((data.days_present / data.total_sessions) * 100).toFixed(2) : 0;
    document.getElementById('percentage').textContent = `${percentage}%`;
    const presentList = document.getElementById('present-list-today');
    presentList.innerHTML = data.present_list_today.length > 0
        ? data.present_list_today.map(name => `<li>${name}</li>`).join('')
        : '<li>No one marked present yet.</li>';
}

function markAttendance() {
    const markBtn = document.getElementById('mark-attendance-btn');
    markBtn.disabled = true;
    markBtn.textContent = 'Getting Location...';
    if (!navigator.geolocation) {
        showAlert('Geolocation is not supported by your browser.');
        markBtn.disabled = false;
        return;
    }
    navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        const device_id = getDeviceId();
        const response = await fetch(`${API_BASE}/api/student/mark_attendance`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: latitude, lon: longitude, device_id }),
        });
        const data = await response.json();
        showAlert(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            markBtn.textContent = 'Marked!';
            updateStudentStats();
        } else {
            markBtn.disabled = false;
            markBtn.textContent = 'Mark My Attendance';
        }
    }, () => {
        showAlert('Could not get location. Please grant permission and ensure location services are enabled.');
        markBtn.disabled = false;
        markBtn.textContent = 'Mark My Attendance';
    });
}

async function requestReRegistration() {
    if (confirm('Are you sure you want to request a device change? You will need to re-register.')) {
        const response = await fetch(`${API_BASE}/api/student/request_reregistration`, { method: 'POST' });
        const data = await response.json();
        showAlert(data.message, data.success ? 'success' : 'error');
    }
}