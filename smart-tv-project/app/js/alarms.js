// Alarms run inside this app, so they can only ring while the app is open and the TV is on.
var Alarms = (function () {
  var CHECK_MS = 5000;
  var MAX_RING_MS = 15 * 60000;
  var TEST_RING_MS = 15000;
  var LATE_LIMIT_MS = 10 * 60000; // a check delayed longer than this skips the alarm
  var DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  // Official 90s R&B music videos by the real artists. One starts at random, then YouTube's
  // autoplay keeps going with similar songs. Each verified to exist (scripts verified via oEmbed).
  var MUSIC = [
    '8WEtxJ4-sh4', // TLC - Waterfalls
    'FrLequ6dUdM', // TLC - No Scrubs
    '3KL9mRus19o', // Blackstreet - No Diggity
    'bQRzrnH6_HY', // Usher - You Make Me Wanna
    'qq09UkPRdFY', // Mariah Carey - Fantasy
    'qSIOp_K5GMw', // Brandy & Monica - The Boy Is Mine
    '0hiUuL5uTKc'  // Montell Jordan - This Is How We Do It
  ];

  var el = UI.el;
  var last = Date.now();
  var snoozeAt = null;
  var ringing = null;
  var audio = null;
  var beepCtx = null;
  var beepGain = null;
  var rampTimer = null;
  var stopTimer = null;
  var returnFocus = null;
  var onRing = function () {};

  function st() { return Store.get(); }

  function at(base, mins) {
    var d = new Date(base);
    d.setHours(Math.floor(mins / 60), mins % 60, 0, 0);
    return d;
  }

  function runsOn(a, d) { return !a.days.length || a.days.indexOf(d.getDay()) !== -1; }

  function nextFor(a, now) {
    for (var i = 0; i < 8; i++) {
      var d = at(now, a.time);
      d.setDate(d.getDate() + i);
      if (d > now && runsOn(a, d)) return d;
    }
    return null;
  }

  function nextTime() {
    var now = new Date(), best = snoozeAt ? new Date(snoozeAt) : null;
    st().alarms.forEach(function (a) {
      if (!a.on) return;
      var d = nextFor(a, now);
      if (d && (!best || d < best)) best = d;
    });
    return best;
  }

  function nextText() {
    var n = nextTime();
    if (!n) return 'No alarm set';
    var today = new Date();
    var tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
    var day = n.toDateString() === today.toDateString() ? 'Today'
      : n.toDateString() === tomorrow.toDateString() ? 'Tomorrow' : DAYS[n.getDay()];
    return 'Alarm: ' + day + ' ' + UI.clock(n.getHours(), n.getMinutes());
  }

  function tick() {
    var now = Date.now();
    if (snoozeAt && snoozeAt <= now) {
      snoozeAt = null;
      ring('Snoozed alarm', false);
    }
    st().alarms.forEach(function (a) {
      if (!a.on) return;
      var t = at(now, a.time).getTime();
      if (t <= last || t > now || !runsOn(a, new Date(t))) return;
      if (now - t < LATE_LIMIT_MS) ring(UI.minutes(a.time), false);
      if (!a.days.length) { a.on = false; Store.save(); draw(); }
    });
    last = now;
  }

  /* Sound: the local file first, then a generated beep if it cannot play. */

  function startBeep(level) {
    var Ctx = window.AudioContext || window.webkitAudioContext;
    if (beepCtx || !Ctx) return;
    audio = null;
    beepCtx = new Ctx();
    beepGain = beepCtx.createGain();
    beepGain.gain.value = 0;
    var osc = beepCtx.createOscillator();
    osc.frequency.value = 880;
    osc.connect(beepGain);
    beepGain.connect(beepCtx.destination);
    osc.start();
    beepGain.level = level;
  }

  function startSound(test) {
    var max = st().alarmMax / 100;
    var rampSec = test ? 5 : st().alarmRamp;
    var began = Date.now();
    function level() { return Math.min(1, (Date.now() - began) / (rampSec * 1000)) * max; }
    audio = new Audio('audio/alarm.wav');
    audio.loop = true;
    audio.volume = 0;
    audio.onerror = function () { startBeep(level); };
    var playing = audio.play();
    if (playing && playing.catch) playing.catch(function () { startBeep(level); });
    rampTimer = setInterval(function () {
      if (audio) audio.volume = level();
      // Half-second pulses, so the fallback reads as an alarm and not a steady tone.
      if (beepGain) beepGain.gain.value = Math.floor(Date.now() / 500) % 2 ? level() * 0.4 : 0;
    }, 250);
  }

  function stopSound() {
    clearInterval(rampTimer);
    if (audio) { audio.onerror = null; audio.pause(); audio = null; }
    if (beepCtx) { beepCtx.close(); beepCtx = null; beepGain = null; }
  }

  /* Ringing screen */

  function finish() {
    clearTimeout(stopTimer);
    stopSound();
    ringing = null;
    document.getElementById('ring').classList.remove('show');
    Nav.scope(null);
    Nav.focus(returnFocus);
    drawAll();
  }

  function snooze() {
    snoozeAt = Date.now() + st().snooze * 60000;
    finish();
  }

  // Opens music in a streaming app. If it will not open, ring the chime so the alarm is never silent.
  function playMusic(label) {
    onRing();
    var appIds = { apple: 'com.apple.applemusic', pandora: 'pandora.lgerp.app' };
    if (appIds[st().alarmSound]) {
      TV.launch(appIds[st().alarmSound], null, function (res) {
        if (res.returnValue === false) ring(label, false, true);
      });
      return;
    }
    var others = MUSIC.filter(function (id) { return id !== st().lastMix; });
    var id = others[Math.floor(Math.random() * others.length)];
    st().lastMix = id;
    Store.save();
    TV.launch('youtube.leanback.v4', { contentTarget: 'v=' + id }, function (res) {
      if (res.returnValue === false) ring(label, false, true);
    });
  }

  function isMusic() { return ['youtube', 'apple', 'pandora'].indexOf(st().alarmSound) !== -1; }

  function ring(label, test, forceChime) {
    if (ringing) return;
    if (!test && !forceChime && isMusic() && TV.available()) {
      playMusic(label);
      return;
    }
    ringing = label;
    onRing();
    returnFocus = Nav.current();
    var box = document.getElementById('ring');
    box.textContent = '';
    var now = new Date();
    box.appendChild(el('div', 'ring-time', UI.clock(now.getHours(), now.getMinutes())));
    box.appendChild(el('div', 'ring-label', test ? 'Test alarm' : label));
    var acts = el('div', 'ring-actions');
    var sn = UI.mini(acts, 'snooze', 'Snooze ' + st().snooze + ' min', snooze);
    UI.mini(acts, 'dismiss', 'Dismiss', finish);
    box.appendChild(acts);
    box.classList.add('show');
    Nav.scope(box);
    Nav.focus(sn);
    startSound(test);
    stopTimer = setTimeout(finish, test ? TEST_RING_MS : MAX_RING_MS);
  }

  /* Alarms screen */

  var listeners = [];
  function drawAll() { draw(); listeners.forEach(function (f) { f(); }); }

  function changed() { Store.save(); drawAll(); }

  function addAlarm() {
    st().alarms.push({ id: String(Date.now()), time: 390, days: [1, 2, 3, 4, 5], on: true });
    changed();
  }

  function card(box, a) {
    box.appendChild(el('div', 'group', 'Alarm'));
    var timeLine = el('div', 'line');
    UI.row(timeLine, 'on-' + a.id, UI.minutes(a.time), a.on ? 'On' : 'Off', function () { a.on = !a.on; changed(); });
    [[-60, '-1 hr'], [60, '+1 hr'], [-5, '-5 min'], [5, '+5 min']].forEach(function (s) {
      UI.mini(timeLine, s[1] + a.id, s[1], function () { a.time = (a.time + s[0] + 1440) % 1440; changed(); });
    });
    box.appendChild(timeLine);
    var dayLine = el('div', 'line');
    DAYS.forEach(function (name, i) {
      UI.mini(dayLine, 'day' + i + a.id, name, function () {
        var at2 = a.days.indexOf(i);
        if (at2 === -1) a.days.push(i); else a.days.splice(at2, 1);
        changed();
      }, a.days.indexOf(i) !== -1);
    });
    box.appendChild(dayLine);
    var acts = el('div', 'line');
    UI.mini(acts, 'test' + a.id, 'Test', function () { ring('Test', true); });
    UI.mini(acts, 'del' + a.id, 'Delete', function () {
      st().alarms.splice(st().alarms.indexOf(a), 1);
      changed();
    });
    if (!a.days.length) acts.appendChild(el('div', 'hint', 'No days picked: rings once'));
    box.appendChild(acts);
  }

  function draw() {
    var box = document.getElementById('alarm-list');
    if (!box) return;
    UI.redraw(box, function () {
      box.appendChild(el('div', 'hint', 'Alarms ring only while this app is open on screen and the TV is on.'));
      var addLine = el('div', 'line');
      UI.row(addLine, 'add', 'Add alarm', undefined, addAlarm);
      UI.mini(addLine, 'test-now', 'Test chime', function () { ring('Test', true); });
      UI.mini(addLine, 'test-music', isMusic() ? 'Test music' : 'Test music (set in Settings)', function () {
        if (isMusic()) playMusic('Test'); else UI.toast('Set "Wake to" to music in Settings first');
      });
      box.appendChild(addLine);
      st().alarms.forEach(function (a) { card(box, a); });
    });
  }

  function build(root) {
    var list = el('div', 'scroll');
    list.id = 'alarm-list';
    root.appendChild(list);
  }

  function init(opts) {
    onRing = opts.onRing;
    var box = el('div');
    box.id = 'ring';
    document.getElementById('app').appendChild(box);
    setInterval(tick, CHECK_MS);
  }

  return {
    init: init,
    build: build,
    draw: draw,
    nextText: nextText,
    onChange: function (f) { listeners.push(f); }
  };
})();
