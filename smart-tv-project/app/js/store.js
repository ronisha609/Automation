// Persistent settings. Stored only in this app's localStorage on the TV.
var Store = (function () {
  var KEY = 'lgdash.settings.v1';

  // Tile colors are plain gradients so the package needs no logo images.
  var APPS = [
    { id: 'com.apple.applemusic', name: 'Apple Music', css: 'linear-gradient(135deg,#fb5c74,#fa233b)' },
    // LG has no YouTube Music app, so this opens the Music channel inside YouTube.
    { id: 'ytmusic', name: 'YT Music', css: '#0f0f0f', image: 'img/ytmusic.svg', launch: 'youtube.leanback.v4',
      params: { contentTarget: 'https://www.youtube.com/tv#/browse?c=UC-9-kyTW8ZkZNDHQJ6FgpwQ' } },
    { id: 'com.apple.appletv', name: 'Apple TV', css: 'linear-gradient(135deg,#3a3a3f,#101012)' },
    { id: 'youtube.leanback.v4', name: 'YouTube', css: 'linear-gradient(135deg,#ff3b30,#c4120a)' },
    { id: 'netflix', name: 'Netflix', css: 'linear-gradient(135deg,#2a0507,#b00710)' },
    { id: 'amazon', name: 'Prime Video', css: 'linear-gradient(135deg,#1aa7dc,#0f6f9e)' },
    { id: 'com.disney.disneyplus-prod', name: 'Disney+', css: 'linear-gradient(135deg,#14306b,#0a1a40)' },
    { id: 'hulu', name: 'Hulu', css: 'linear-gradient(135deg,#1ce783,#0f9a57)', dark: true },
    { id: 'com.wbd.stream', name: 'HBO Max', css: 'linear-gradient(135deg,#5b2be0,#2a1280)' },
    { id: 'com.peacock.tv', name: 'Peacock', css: 'linear-gradient(135deg,#2b2b33,#000)' },
    { id: 'com.webos.app.livetv', name: 'Live TV', css: 'linear-gradient(135deg,#46505f,#232832)' },
    { id: 'youtube.leanback.ytv.v1', name: 'YouTube TV', css: 'linear-gradient(135deg,#d81f26,#7c0f13)' },
    { id: 'com.plutotv.app', name: 'Pluto TV', css: 'linear-gradient(135deg,#ffcc00,#f09000)', dark: true },
    { id: 'com.cbs-all-access.webapp.prod', name: 'Paramount+', css: 'linear-gradient(135deg,#0d6efd,#0a3fa8)' },
    { id: 'com.tiktok.app.tv', name: 'TikTok', css: 'linear-gradient(135deg,#25f4ee,#fe2c55)' },
    { id: 'com.twin.app.homegym', name: 'LG Fitness', css: 'linear-gradient(135deg,#ff7a45,#c43d10)' },
    { id: 'airplay', name: 'AirPlay', css: 'linear-gradient(135deg,#5b6472,#2a2f38)' },
    { id: 'com.webos.app.browser', name: 'Web Browser', css: 'linear-gradient(135deg,#3c8dde,#1b4f8a)' }
  ];

  var HOME_APPS = ['hulu', 'netflix', 'amazon', 'com.apple.appletv', 'youtube.leanback.ytv.v1', 'com.apple.applemusic', 'ytmusic', 'youtube.leanback.v4'];

  var BACKGROUNDS = [
    { id: 'ember', name: 'Ember' },
    { id: 'copper', name: 'Copper' },
    { id: 'dusk', name: 'Dusk' },
    { id: 'midnight', name: 'Midnight' },
    { id: 'forest', name: 'Forest' },
    { id: 'slate', name: 'Slate' },
    { id: 'black', name: 'Black' }
  ];

  // Bump to replace the shortcuts already saved on the TV.
  var LAYOUT_REV = 5;

  // A neutral default; change it in Settings. The app stores your real location only on the TV.
  var DEFAULT_LOCATION = { name: 'New York', detail: 'New York, United States', lat: 40.7128, lon: -74.006 };

  function defaults() {
    return {
      clock24: false,
      tempUnit: 'F',
      bg: 'ember',
      location: DEFAULT_LOCATION,
      apps: defaultApps(),
      layoutRev: LAYOUT_REV,
      weatherCache: null,
      alarms: [],
      alarmSound: 'apple',
      lastMix: '',
      alarmMax: 80,
      alarmRamp: 60,
      snooze: 9,
      nightColor: 'amber',
      sleepMin: 30,
      schedOn: false,
      schedStart: 480,
      schedEnd: 960,
      saverOn: true,
      saverDelay: 3,
      guest: null
    };
  }

  function defaultApps() {
    var rest = APPS.filter(function (a) { return HOME_APPS.indexOf(a.id) === -1; });
    return HOME_APPS.map(function (id) { return { id: id, on: true }; })
      .concat(rest.map(function (a) { return { id: a.id, on: false }; }));
  }

  function load() {
    var d = defaults(), saved = null;
    try { saved = JSON.parse(localStorage.getItem(KEY)); } catch (e) { saved = null; }
    if (!saved) return d;
    if (saved.alarmSound === 'music') saved.alarmSound = 'youtube'; // old two-way setting
    var fresh = saved.layoutRev === LAYOUT_REV;
    Object.keys(d).forEach(function (k) {
      if (!fresh && (k === 'apps' || k === 'layoutRev')) return;
      if (saved[k] !== undefined && saved[k] !== null) d[k] = saved[k];
    });
    // Keep the saved order, and pick up any apps added by a later version.
    var known = d.apps.map(function (a) { return a.id; });
    APPS.forEach(function (a) {
      if (known.indexOf(a.id) === -1) d.apps.push({ id: a.id, on: false });
    });
    return d;
  }

  var state = load();

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* keeps working for this session */ }
  }

  function reset() {
    state = defaults();
    save();
    return state;
  }

  function appInfo(id) {
    return APPS.filter(function (a) { return a.id === id; })[0];
  }

  return {
    get: function () { return state; },
    save: save,
    reset: reset,
    appInfo: appInfo,
    BACKGROUNDS: BACKGROUNDS
  };
})();
