// ─── Flash messages auto-dismiss ────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash-msg');
  flashes.forEach(f => {
    setTimeout(() => {
      f.style.transition = 'opacity 0.5s, transform 0.5s';
      f.style.opacity = '0';
      f.style.transform = 'translateX(20px)';
      setTimeout(() => f.remove(), 500);
    }, 4000);
  });

  // ─── Checkbox item toggle ────────────────────────────────────
  document.querySelectorAll('.checkbox-item').forEach(item => {
    item.addEventListener('click', () => {
      const cb = item.querySelector('input[type="checkbox"]');
      if (cb) cb.checked = !cb.checked;
    });
  });

  // ─── Modal open/close ────────────────────────────────────────
  document.querySelectorAll('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.modal;
      const overlay = document.getElementById(id);
      if (overlay) overlay.classList.add('open');
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) overlay.classList.remove('open');
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.modal-overlay').classList.remove('open');
    });
  });

  // ─── Preferred staff dynamic load ───────────────────────────
  const softwareSelect = document.getElementById('software_id');
  const preferredSelect = document.getElementById('preferred_staff_id');
  if (softwareSelect && preferredSelect) {
    softwareSelect.addEventListener('change', () => {
      const swId = softwareSelect.value;
      preferredSelect.innerHTML = '<option value="">-- None --</option>';
      if (!swId) return;
      fetch(`/customer/api/staff-for-software/${swId}`)
        .then(r => r.json())
        .then(data => {
          data.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.name;
            preferredSelect.appendChild(opt);
          });
        });
    });
  }

  // ─── Transfer modal – inject ticket id ──────────────────────
  document.querySelectorAll('[data-transfer-ticket]').forEach(btn => {
    btn.addEventListener('click', () => {
      const ticketId = btn.dataset.transferTicket;
      const form = document.getElementById('transfer-form');
      if (form) form.action = `/staff/ticket/${ticketId}/transfer`;
    });
  });
});
