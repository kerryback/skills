// Course setup: roster name edits and per-student photo swaps. The roster
// itself is read from the course folder by Claude, not uploaded here.

(function () {
  const roster = document.getElementById('roster');
  const saveRoster = document.getElementById('save-roster');
  if (!roster || !saveRoster) return;

  const courseId = roster.dataset.courseId;
  const markDirty = () => { saveRoster.disabled = false; };

  roster.addEventListener('input', (e) => {
    if (e.target.classList.contains('rname')) markDirty();
  });

  roster.addEventListener('click', (e) => {
    const button = e.target.closest('[data-remove]');
    if (!button) return;
    const row = button.closest('.roster-row');
    const removed = row.classList.toggle('removed');
    button.textContent = removed ? 'Undo' : 'Remove';
    markDirty();
  });

  roster.addEventListener('change', async (e) => {
    const input = e.target.closest('[data-photo-for]');
    if (!input || !input.files.length) return;
    const body = new FormData();
    body.append('photo', input.files[0]);
    const id = input.dataset.photoFor;
    try {
      const response = await fetch(`/courses/${courseId}/students/${id}/photo`, {
        method: 'POST', body,
      });
      if (!response.ok) throw new Error();
      toast('Photo replaced.');
      window.location.reload();
    } catch (err) {
      toast('Could not replace that photo.', true);
    }
  });

  saveRoster.addEventListener('click', async () => {
    const students = [];
    const remove = [];
    roster.querySelectorAll('.roster-row').forEach((row) => {
      const id = Number(row.dataset.studentId);
      if (row.classList.contains('removed')) {
        remove.push(id);
      } else {
        students.push({ id, name: row.querySelector('.rname').value });
      }
    });
    if (remove.length && !confirm(`Remove ${remove.length} student(s) from the roster?`)) return;

    saveRoster.disabled = true;
    try {
      const response = await fetch(`/courses/${courseId}/students`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ students, delete: remove }),
      });
      if (!response.ok) throw new Error();
      toast('Roster saved.');
      window.location.reload();
    } catch (err) {
      toast('Could not save the roster.', true);
      saveRoster.disabled = false;
    }
  });
})();
