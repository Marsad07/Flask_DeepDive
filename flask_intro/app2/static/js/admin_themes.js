//  Colour pickers
// Remove duplicate hidden inputs (Jinja loop creates two inputs per field)
// We only want the hidden one submitted
document.querySelectorAll('input[type="color"]').forEach(picker => {
  picker.addEventListener('input', function() {
    const target = this.dataset.target;
    const hex    = this.value;

    // Update hidden input
    document.getElementById('hidden-' + target).value = hex;

    // Update hex label
    const hexLabel = document.querySelector(`.colour-hex[data-for="${target}"]`);
    if (hexLabel) hexLabel.textContent = hex;

    // Apply live to :root
    const map = {
      color_primary:     '--color-primary',
      color_accent:      '--color-accent',
      color_background:  '--color-bg',
      color_surface:     '--color-surface',
      color_text:        '--color-text',
      color_text_muted:  '--color-text-muted',
      color_sidebar_bg:  '--color-sidebar-bg',
      color_sidebar_text:'--color-sidebar-text',
    };
    if (map[target]) {
      document.documentElement.style.setProperty(map[target], hex);
    }
    updatePreviewBar();
  });
});

//  Preview bar
function updatePreviewBar() {
  const getVar = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const primary = getVar('--color-primary');
  const accent  = getVar('--color-accent');
  const text    = getVar('--color-text');
  const surface = getVar('--color-surface');
  const radius  = getVar('--radius') || '2px';

  const pb = document.getElementById('prev-btn-primary');
  pb.style.background   = primary;
  pb.style.color        = accent;
  pb.style.borderRadius = radius;

  const ab = document.getElementById('prev-btn-accent');
  ab.style.background   = accent;
  ab.style.color        = text;
  ab.style.borderRadius = radius;

  const badge = document.getElementById('prev-badge');
  badge.style.background = primary + '22';
  badge.style.color      = primary;
}
updatePreviewBar();

// Font selects
function loadGoogleFont(family) {
  const id  = 'gfont-' + family.replace(/\s/g,'-');
  if (!document.getElementById(id)) {
    const link = document.createElement('link');
    link.id   = id;
    link.rel  = 'stylesheet';
    link.href = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family)}:wght@400;700&display=swap`;
    document.head.appendChild(link);
  }
}

document.getElementById('font-body-select').addEventListener('change', function() {
  loadGoogleFont(this.value);
  document.documentElement.style.setProperty('--font-body', `'${this.value}', sans-serif`);
  document.getElementById('prev-body').style.fontFamily = this.value;
});

document.getElementById('font-heading-select').addEventListener('change', function() {
  loadGoogleFont(this.value);
  document.documentElement.style.setProperty('--font-heading', `'${this.value}', serif`);
  document.getElementById('prev-heading').style.fontFamily = this.value;
});

// Border radius
document.getElementById('radius-select').addEventListener('change', function() {
  document.documentElement.style.setProperty('--radius', this.value);
  updatePreviewBar();
});

// Preset buttons
document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', function() {
    const map = {
      color_primary:     '--color-primary',
      color_accent:      '--color-accent',
      color_background:  '--color-bg',
      color_surface:     '--color-surface',
      color_text:        '--color-text',
      color_text_muted:  '--color-text-muted',
      color_sidebar_bg:  '--color-sidebar-bg',
      color_sidebar_text:'--color-sidebar-text',
    };
    Object.entries(map).forEach(([dataKey, cssVar]) => {
      const val = this.dataset[dataKey.replace('color_','')];
      if (val) {
        document.documentElement.style.setProperty(cssVar, val);
        // Update picker + hidden input
        const picker = document.querySelector(`input[type="color"][data-target="${dataKey}"]`);
        const hidden = document.getElementById('hidden-' + dataKey);
        const label  = document.querySelector(`.colour-hex[data-for="${dataKey}"]`);
        if (picker) picker.value = val;
        if (hidden) hidden.value = val;
        if (label)  label.textContent = val;
      }
    });
    updatePreviewBar();
  });
});

// Reset to defaults
document.getElementById('reset-btn').addEventListener('click', function() {
  if (!confirm('Reset theme to original defaults?')) return;
  const defaults = {
    color_primary:     '#8B0000',
    color_accent:      '#D4AF37',
    color_background:  '#F7F4EE',
    color_surface:     '#FFFFFF',
    color_text:        '#2C2416',
    color_text_muted:  '#9E8C78',
    color_sidebar_bg:  '#2C2416',
    color_sidebar_text:'#FFFEF2',
  };
  const cssMap = {
    color_primary:     '--color-primary',
    color_accent:      '--color-accent',
    color_background:  '--color-bg',
    color_surface:     '--color-surface',
    color_text:        '--color-text',
    color_text_muted:  '--color-text-muted',
    color_sidebar_bg:  '--color-sidebar-bg',
    color_sidebar_text:'--color-sidebar-text',
  };
  Object.entries(defaults).forEach(([key, val]) => {
    document.getElementById('hidden-' + key).value = val;
    const picker = document.querySelector(`[data-target="${key}"]`);
    const label  = document.querySelector(`.colour-hex[data-for="${key}"]`);
    if (picker) picker.value = val;
    if (label)  label.textContent = val;
    document.documentElement.style.setProperty(cssMap[key], val);
  });
  updatePreviewBar();
});