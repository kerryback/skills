// Scores screen: the course picker, score pips, the date field, saving, and
// the don't-lose-your-work guard.

(function () {
  const bar = document.getElementById('evalbar');
  if (!bar) return;

  const courseSelect = document.getElementById('course-select');
  const courseId = bar.dataset.courseId;
  const grid = document.getElementById('grid');
  const dateInput = document.getElementById('date');
  const saveBtn = document.getElementById('save-btn');
  const dirtyFlag = document.getElementById('dirty');
  const todayBtn = document.getElementById('today-btn');

  let dirty = false;
  let leaving = false;          // set while we navigate on purpose

  // The course picker is present even with no course chosen; everything below
  // it only exists once there is one to score.
  if (courseSelect) {
    let lastCourse = courseSelect.value;
    courseSelect.addEventListener('change', () => {
      const next = courseSelect.value;
      if (!next || next === lastCourse) return;
      if (!confirmLeave()) { courseSelect.value = lastCourse; return; }
      leaving = true;
      window.location.href = `/?course=${encodeURIComponent(next)}`;
    });
  }

  if (!dateInput || !saveBtn) return;   // no course chosen, or no roster yet

  let lastDate = dateInput.value;

  function setDirty(value) {
    dirty = value;
    dirtyFlag.hidden = !value;
    saveBtn.textContent = value ? 'Save' : 'Saved';
    saveBtn.classList.toggle('primary', true);
  }

  function confirmLeave() {
    if (!dirty) return true;
    return window.confirm(
      'You have unsaved participation scores.\n\n' +
      'Click Cancel to go back and save, or OK to discard them.'
    );
  }

  function go(url) {
    if (!confirmLeave()) return false;
    leaving = true;
    window.location.href = url;
    return true;
  }

  // --- scoring ---

  if (grid) {
    grid.addEventListener('click', (event) => {
      const pip = event.target.closest('.pip');
      if (!pip) return;
      const group = pip.parentElement;
      const wasOn = pip.classList.contains('on');
      group.querySelectorAll('.pip').forEach((p) => {
        p.classList.remove('on');
        p.setAttribute('aria-pressed', 'false');
      });
      if (!wasOn) {                       // clicking the active score clears it
        pip.classList.add('on');
        pip.setAttribute('aria-pressed', 'true');
      }
      pip.closest('.card').classList.add('touched');
      setDirty(true);
    });

    grid.addEventListener('input', (event) => {
      if (event.target.classList.contains('notes')) {
        event.target.closest('.card').classList.add('touched');
        setDirty(true);
      }
    });
  }

  // --- date ---

  dateInput.addEventListener('change', () => {
    const next = dateInput.value;
    if (!next) { dateInput.value = lastDate; return; }
    if (next === lastDate) return;
    if (!confirmLeave()) { dateInput.value = lastDate; return; }
    leaving = true;
    window.location.href = `/evaluate/${courseId}?date=${encodeURIComponent(next)}`;
  });

  todayBtn.addEventListener('click', () => {
    const today = todayBtn.dataset.today;
    if (today === dateInput.value) return;
    dateInput.value = today;
    dateInput.dispatchEvent(new Event('change'));
  });

  // --- saving ---

  function collect() {
    return Array.from(document.querySelectorAll('.card')).map((card) => {
      const pick = (field) => {
        const on = card.querySelector(`.score[data-field="${field}"] .pip.on`);
        return on ? on.dataset.value : '';
      };
      return {
        id: Number(card.dataset.studentId),
        amount: pick('amount'),
        quality: pick('quality'),
        notes: card.querySelector('.notes').value,
      };
    });
  }

  async function save() {
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving…';
    try {
      const response = await fetch(`/api/courses/${courseId}/evaluations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: dateInput.value, entries: collect() }),
      });
      const data = await response.json();
      if (!response.ok) {
        toast(data.error || 'Save failed.', true);
        setDirty(true);
        return;
      }
      setDirty(false);
      document.querySelectorAll('.card.touched').forEach((c) => c.classList.remove('touched'));
      const n = data.saved;
      toast(`Saved ${n} row${n === 1 ? '' : 's'} for ${data.date} → ${data.path}`);
    } catch (err) {
      toast('Save failed — is the app still running?', true);
      setDirty(true);
    } finally {
      saveBtn.disabled = false;
      if (!dirty) saveBtn.textContent = 'Saved';
    }
  }

  saveBtn.addEventListener('click', save);

  document.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === 's') {
      event.preventDefault();
      save();
    }
  });

  // --- leave guard ---

  document.querySelectorAll('a[data-guard], .topbar a').forEach((link) => {
    link.addEventListener('click', (event) => {
      if (!dirty) return;
      event.preventDefault();
      go(link.href);
    });
  });

  window.addEventListener('beforeunload', (event) => {
    if (!dirty || leaving) return;
    event.preventDefault();
    event.returnValue = '';   // triggers the browser's own "Leave site?" prompt
    return '';
  });

  setDirty(false);
  saveBtn.textContent = 'Save';
})();
