
const modalOverlay = document.getElementById('modalOverlay');
const modalContent = document.getElementById('modalContent');
const modalTitle = document.getElementById('modalTitle');
const modalForm = document.getElementById('modalForm');
const modalClose = document.getElementById('modalClose');
const joinCallBtn = document.getElementById('joinCallBtn');

function openModal(type) {
    modalOverlay.style.display = 'flex';
    modalForm.reset();
    if (type === 'create') {
    modalTitle.textContent = 'Create a New Call';
    } else if (type === 'join') {
    modalTitle.textContent = 'Join an Existing Call';
    }
}

function closeModal() {
    modalOverlay.style.display = 'none';
}

document.getElementById("createCallBtn").addEventListener("click", () => {
    window.location.href = "../meetingroom/Meetingroom.html";
    });
joinCallBtn.addEventListener('click', () => openModal('join'));
modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
});

modalForm.addEventListener('submit', (e) => {
    e.preventDefault();
    alert(modalTitle.textContent + ' functionality coming soon!');
    closeModal();
});

