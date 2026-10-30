// Screens, clock, weather display and Settings. Plain ES5 for webOS 4's old Chromium.
(function () {
  var WEATHER_REFRESH_MS = 30 * 60 * 1000;
  var TABS = [
    { id: 'home', name: 'Home' },
    { id: 'night', name: 'Night' },
    { id: 'alarms', name: 'Alarms' },
    { id: 'agenda', name: 'Agenda' },
    { id: 'workout', name: 'Workout' },
    { id: 'guest', name: 'Guest' },
    { id: 'settings', name: 'Settings' }
  ];

  var s = Store.get();
  var app = document.getElementById('app');
  var screens = document.getElementById('screens');
  var activeTab = 'home';
  var tabEls = {};
  var lastFocus = {};
  var results = [];
  var query = '';
  var note = '';
  var searching = false;
  var resetArmed = false;
  var exitArmedAt = 0;
  var el = UI.el;
  var pad = UI.pad;
  var toast = UI.toast;

  /* Clock */

  function timeParts(d) {
    var h = d.getHours();
    if (s.clock24) return { time: pad(h) + ':' + pad(d.getMinutes()), ampm: '' };
    return { time: (h % 12 || 12) + ':' + pad(d.getMinutes()), ampm: h < 12 ? 'AM' : 'PM' };
  }

  function drawClock() {
    var d = new Date(), p = timeParts(d);
    var dateText = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    var time = document.getElementById('time');
    time.textContent = p.time;
    if (p.ampm) time.appendChild(el('span', '', p.ampm)).id = 'ampm';
    document.getElementById('date').textContent = dateText;
    document.getElementById('night-time').textContent = p.time + (p.ampm ? ' ' + p.ampm : '');
    document.getElementById('night-date').textContent = dateText;
    document.getElementById('topclock').textContent = activeTab === 'home' || activeTab === 'night' ? '' : p.time + (p.ampm ? ' ' + p.ampm : '');
  }

  function startClock() {
    drawClock();
    Night.minute();
    setTimeout(startClock, 60000 - (Date.now() % 60000) + 50);
  }

  /* Weather */

  function drawWeather() {
    var temp = document.getElementById('wx-temp');
    var text = document.getElementById('wx-text');
    var sub = document.getElementById('wx-sub');
    var c = s.weatherCache;
    if (!s.location) {
      temp.textContent = '';
      text.textContent = 'No weather location';
      sub.textContent = 'Add one in Settings';
    } else if (!c || c.unit !== s.tempUnit) {
      temp.textContent = '';
      text.textContent = s.location.name;
      sub.textContent = 'Weather unavailable' + (Weather.lastError() ? ' (' + Weather.lastError() + ')' : '');
    } else {
      var age = new Date(c.at);
      temp.textContent = c.temp + '°';
      text.textContent = Weather.label(c.code) + ' · ' + s.location.name;
      sub.textContent = 'H ' + c.high + '°  L ' + c.low + '°  ·  Updated ' + timeParts(age).time + (timeParts(age).ampm ? ' ' + timeParts(age).ampm : '');
    }
  }

  function refreshWeather() {
    if (!s.location) { drawWeather(); return; }
    Weather.fetchNow(s.location, s.tempUnit, function (w) {
      if (w) { s.weatherCache = w; Store.save(); }
      drawWeather();
    });
  }

  /* Home */

  function launch(info) {
    if (!TV.available()) { toast('Preview only: would open ' + info.name); return; }
    TV.launch(info.launch || info.id, info.params, function (res) {
      if (res.returnValue === false) toast('Could not open ' + info.name);
    });
  }

  function drawTiles() {
    var box = document.getElementById('tiles');
    box.textContent = '';
    s.apps.forEach(function (a) {
      var info = Store.appInfo(a.id);
      if (!a.on || !info) return;
      // Real logos come from the TV (scripts/fetch_logos.py); without one the tile shows its name.
      var logo = window.LOGOS && window.LOGOS[a.id];
      var src = info.image || (logo && logo.file);
      var t = el('div', 'tile f', src ? '' : info.name);
      t.style.background = logo && logo.color ? logo.color : info.css;
      t.style.color = info.dark ? '#0b0d12' : '#fff';
      if (src) {
        var img = el('img');
        img.src = src;
        img.alt = info.name;
        t.appendChild(img);
      }
      t.onok = function () { launch(info); };
      box.appendChild(t);
    });
  }

  function buildHome(root) {
    var hero = el('div');
    hero.id = 'hero';
    var left = el('div');
    var time = el('div');
    time.id = 'time';
    var date = el('div');
    date.id = 'date';
    left.appendChild(time);
    left.appendChild(date);
    var wx = el('div');
    wx.id = 'weather';
    ['wx-temp', 'wx-text', 'wx-sub'].forEach(function (id) {
      var d = el('div');
      d.id = id;
      wx.appendChild(d);
    });
    hero.appendChild(left);
    hero.appendChild(wx);
    root.appendChild(hero);
    var tiles = el('div', 'scroll');
    tiles.id = 'tiles';
    root.appendChild(tiles);
  }

  /* Placeholder screens */

  function buildStub(root, title, text) {
    root.classList.add('stub');
    root.appendChild(el('h1', '', title));
    root.appendChild(el('p', '', text));
    root.appendChild(el('div', 'badge', 'PLACEHOLDER'));
  }

  /* Settings */

  function row(parent, label, value, onok) {
    var r = el('div', 'row f');
    r.appendChild(el('span', '', label));
    if (value !== undefined) r.appendChild(el('span', 'val', value));
    r.onok = onok;
    parent.appendChild(r);
    return r;
  }

  function line(parent, label, value, onok) {
    var l = el('div', 'line');
    row(l, label, value, onok);
    parent.appendChild(l);
    return l;
  }

  function applyBackground() {
    app.className = 'bg-' + (activeTab === 'night' ? 'black' : s.bg);
  }

  function changed(after) {
    Store.save();
    if (after) after();
    drawSettings();
  }

  function cycleBackground() {
    var list = Store.BACKGROUNDS;
    var i = list.map(function (b) { return b.id; }).indexOf(s.bg);
    s.bg = list[(i + 1) % list.length].id;
    changed(applyBackground);
  }

  function runSearch(input) {
    var q = input.value.replace(/^\s+|\s+$/g, '');
    input.onblur = null;
    input.blur();
    if (!q || searching) return;
    query = q;
    note = '';
    searching = true;
    results = [];
    drawSettings();
    Weather.search(q, function (found) {
      searching = false;
      results = found || [];
      if (!found) note = 'Search failed (' + Weather.lastError() + ')';
      else if (!found.length) note = 'No places found for "' + q + '". Try just the town name.';
      drawSettings();
      var first = document.querySelector('[data-key="result0"]');
      if (first) Nav.focus(first);
    });
  }

  function chooseLocation(r) {
    s.location = {
      name: r.name,
      detail: [r.admin1, r.country].filter(Boolean).join(', '),
      lat: r.latitude,
      lon: r.longitude
    };
    s.weatherCache = null;
    results = [];
    query = '';
    changed(refreshWeather);
  }

  function cycleLine(box, key, label, field, options, show) {
    line(box, label, show(s[field]), function () {
      s[field] = options[(options.indexOf(s[field]) + 1) % options.length];
      changed();
    }).firstChild.setAttribute('data-key', key);
  }

  function timeLine(box, field, label) {
    var l = line(box, label, UI.minutes(s[field]), function () {});
    l.firstChild.classList.remove('f');
    [[-30, '-30 min'], [30, '+30 min']].forEach(function (step) {
      UI.mini(l, step[1] + field, step[1], function () {
        s[field] = (s[field] + step[0] + 1440) % 1440;
        changed(Night.minute);
      });
    });
  }

  function moveApp(i) {
    if (i === 0) return;
    var a = s.apps.splice(i, 1)[0];
    s.apps.splice(i - 1, 0, a);
    changed(drawTiles);
  }

  function drawSettings() {
    var box = document.getElementById('settings-list');
    var keep = Nav.current() && Nav.current().getAttribute('data-key');
    var scroll = box.scrollTop;
    box.textContent = '';

    box.appendChild(el('div', 'group', 'Clock and weather'));
    line(box, 'Clock format', s.clock24 ? '24-hour' : '12-hour', function () {
      s.clock24 = !s.clock24;
      changed(function () { drawClock(); drawWeather(); });
    }).firstChild.setAttribute('data-key', 'clock');
    line(box, 'Temperature', '°' + s.tempUnit, function () {
      s.tempUnit = s.tempUnit === 'F' ? 'C' : 'F';
      changed(refreshWeather);
    }).firstChild.setAttribute('data-key', 'unit');

    box.appendChild(el('div', 'group', 'Weather location: ' + (s.location ? s.location.name + (s.location.detail ? ', ' + s.location.detail : '') : 'not set')));
    var wrap = el('div', 'line');
    var input = el('input', 'row f');
    input.type = 'text';
    input.placeholder = 'Search for a city, then press OK on the keyboard';
    input.value = query;
    input.setAttribute('data-key', 'search');
    input.onok = function () { input.focus(); };
    // The on-screen keyboard can close without sending Enter.
    input.onblur = function () { runSearch(input); };
    wrap.appendChild(input);
    box.appendChild(wrap);
    if (searching || note) box.appendChild(el('div', 'group', searching ? 'Searching...' : note));
    results.forEach(function (r, i) {
      line(box, r.name, [r.admin1, r.country].filter(Boolean).join(', '), function () {
        chooseLocation(r);
      }).firstChild.setAttribute('data-key', 'result' + i);
    });

    box.appendChild(el('div', 'group', 'Appearance'));
    var bgName = Store.BACKGROUNDS.filter(function (b) { return b.id === s.bg; })[0].name;
    line(box, 'Background', bgName, cycleBackground).firstChild.setAttribute('data-key', 'bg');
    line(box, 'Ambient screensaver', s.saverOn ? 'On' : 'Off', function () {
      s.saverOn = !s.saverOn;
      changed();
    }).firstChild.setAttribute('data-key', 'saver');
    cycleLine(box, 'saverdelay', 'Screensaver starts after', 'saverDelay', [1, 3, 5, 10], function (v) { return v + ' min idle'; });

    box.appendChild(el('div', 'group', 'Night'));
    line(box, 'Night text color', s.nightColor === 'gray' ? 'Gray' : 'Amber', function () {
      s.nightColor = s.nightColor === 'gray' ? 'amber' : 'gray';
      changed(Night.draw);
    }).firstChild.setAttribute('data-key', 'ncolor');
    cycleLine(box, 'nsleep', 'Bedtime sleep timer', 'sleepMin', [0, 15, 30, 60, 90], function (v) { return v ? v + ' min' : 'Off'; });
    line(box, 'Auto Night schedule', s.schedOn ? 'On' : 'Off', function () {
      s.schedOn = !s.schedOn;
      changed(Night.minute);
    }).firstChild.setAttribute('data-key', 'sched');
    timeLine(box, 'schedStart', 'Night starts');
    timeLine(box, 'schedEnd', 'Night ends');

    box.appendChild(el('div', 'group', 'Alarm sound'));
    var sounds = ['pandora', 'apple', 'youtube', 'chime'];
    var soundNames = { pandora: 'Pandora', apple: 'Apple Music', youtube: '90s/2000s R&B and hip-hop', chime: 'Chime' };
    line(box, 'Wake to', soundNames[s.alarmSound], function () {
      s.alarmSound = sounds[(sounds.indexOf(s.alarmSound) + 1) % sounds.length];
      changed();
    }).firstChild.setAttribute('data-key', 'asound');
    cycleLine(box, 'amax', 'Maximum volume', 'alarmMax', [20, 40, 60, 80, 100], function (v) { return v + '% of TV volume'; });
    cycleLine(box, 'aramp', 'Volume ramp', 'alarmRamp', [15, 30, 60, 120], function (v) { return v + ' sec'; });
    cycleLine(box, 'asnooze', 'Snooze', 'snooze', [5, 9, 10, 15], function (v) { return v + ' min'; });

    box.appendChild(el('div', 'group', 'Home shortcuts'));
    s.apps.forEach(function (a, i) {
      var info = Store.appInfo(a.id);
      if (!info) return;
      var l = line(box, info.name, a.on ? 'On' : 'Off', function () {
        a.on = !a.on;
        changed(drawTiles);
      });
      l.firstChild.setAttribute('data-key', 'app-' + a.id);
      var up = el('div', 'row mini f', 'Move up');
      up.setAttribute('data-key', 'up-' + a.id);
      up.onok = function () { moveApp(i); };
      l.appendChild(up);
    });

    box.appendChild(el('div', 'group', 'Reset'));
    var r = line(box, resetArmed ? 'Press OK again to erase all settings' : 'Reset all settings', undefined, function () {
      if (!resetArmed) { resetArmed = true; drawSettings(); return; }
      resetArmed = false;
      s = Store.reset();
      applyBackground();
      drawTiles();
      drawClock();
      drawWeather();
      drawSettings();
      toast('Settings reset');
    });
    r.firstChild.setAttribute('data-key', 'reset');

    box.scrollTop = scroll;
    if (activeTab === 'settings' && keep && keep !== 'tab') {
      Nav.focus(box.querySelector('[data-key="' + keep + '"]') || box.querySelector('.f'));
    }
  }

  function buildSettings(root) {
    var list = el('div', 'scroll');
    list.id = 'settings-list';
    root.appendChild(list);
    var about = el('div');
    about.id = 'about';
    about.appendChild(el('b', '', 'LG Dashboard 1.2.0'));
    about.appendChild(el('div', '', 'No accounts, ads or tracking. Settings stay on this TV. Weather comes from Open-Meteo.'));
    root.appendChild(about);
  }

  /* Tabs and keys */

  function showTab(id) {
    if (id === activeTab) return;
    activeTab = id;
    resetArmed = false;
    TABS.forEach(function (t) {
      tabEls[t.id].classList.toggle('active', t.id === id);
      document.getElementById('screen-' + t.id).classList.toggle('active', t.id === id);
    });
    applyBackground();
    drawClock();
    if (id === 'settings') drawSettings();
    if (id === 'night') Night.draw();
    if (id === 'alarms') Alarms.draw();
    if (id === 'guest') Guest.draw();
  }

  function buildTabs() {
    var nav = document.getElementById('tabs');
    TABS.forEach(function (t) {
      var tab = el('div', 'tab f' + (t.id === 'home' ? ' active' : ''), t.name);
      tab.setAttribute('data-key', 'tab');
      tab.onfocused = function () { showTab(t.id); };
      nav.appendChild(tab);
      tabEls[t.id] = tab;
      var sec = el('section', 'screen' + (t.id === 'home' ? ' active' : ''));
      sec.id = 'screen-' + t.id;
      screens.appendChild(sec);
    });
  }

  function onBack() {
    var cur = Nav.current();
    if (activeTab !== 'home') {
      Nav.focus(tabEls.home);
      return;
    }
    if (cur && cur.classList.contains('tile')) {
      Nav.focus(tabEls.home);
      return;
    }
    if (Date.now() - exitArmedAt < 3000) { TV.exit(); return; }
    exitArmedAt = Date.now();
    toast('Press Back again to exit');
  }

  // The PC can send settings at launch (scripts/push_config.py).
  function applyParams(p) {
    if (!p) return;
    if (p.guestWifi) {
      s.guest = p.guestWifi;
      Store.save();
      Guest.draw();
      toast('Guest Wi-Fi saved');
    }
    if (p.alarmSound) {
      s.alarmSound = p.alarmSound;
      Store.save();
      if (activeTab === 'settings') drawSettings();
      toast('Alarm sound set');
    }
    if (p.addAlarm) {
      var d = new Date();
      var mins = (d.getHours() * 60 + d.getMinutes() + (p.addAlarm.inMinutes || 2)) % 1440;
      s.alarms.push({ id: String(Date.now()), time: mins, days: [], on: true });
      Store.save();
      Alarms.draw();
      toast('Test alarm set for ' + UI.minutes(mins));
    }
    if (p.setAlarm) {
      s.alarms = [{ id: String(Date.now()), time: p.setAlarm.time, days: p.setAlarm.days || [], on: true }];
      Store.save();
      Alarms.draw();
      toast('Alarm set for ' + UI.minutes(p.setAlarm.time));
    }
    if (p.schedule) {
      if (p.schedule.on !== undefined) s.schedOn = p.schedule.on;
      if (p.schedule.start !== undefined) s.schedStart = p.schedule.start;
      if (p.schedule.end !== undefined) s.schedEnd = p.schedule.end;
      Store.save();
      if (activeTab === 'settings') drawSettings();
      Night.minute();
      toast('Night schedule updated');
    }
  }

  function start() {
    buildTabs();
    var get = function (id) { return document.getElementById('screen-' + id); };
    buildHome(get('home'));
    Night.build(get('night'));
    Alarms.build(get('alarms'));
    buildStub(get('agenda'), 'Agenda', 'Your calendars and tasks will appear here in Stage 3.');
    buildStub(get('workout'), 'Workout', 'The workout screen is planned for Stage 4.');
    Guest.build(get('guest'));
    buildSettings(get('settings'));

    applyBackground();
    drawTiles();
    drawWeather();
    Alarms.init({ onRing: function () { Screensaver.activity(); Night.wake(); } });
    Screensaver.init();
    Alarms.onChange(Night.draw);
    Night.init({ show: function (id) { Nav.focus(tabEls[id]); } });
    Nav.init({
      back: onBack,
      inputDone: runSearch,
      activity: Screensaver.activity,
      anyKey: Night.wake
    });
    Nav.focus(document.querySelector('.tile') || tabEls.home);
    startClock();
    Guest.draw();
    applyParams(TV.launchParams());
    document.addEventListener('webOSRelaunch', function (e) { applyParams(e.detail); });
    refreshWeather();
    setInterval(refreshWeather, WEATHER_REFRESH_MS);
  }

  start();
})();
