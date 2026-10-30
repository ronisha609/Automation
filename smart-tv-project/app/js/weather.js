// Weather from Open-Meteo. It needs no key or account; requests carry only coordinates or the search text.
var Weather = (function () {
  var TEXT = {
    0: 'Clear', 1: 'Mostly clear', 2: 'Partly cloudy', 3: 'Cloudy', 45: 'Fog', 48: 'Fog',
    51: 'Light drizzle', 53: 'Drizzle', 55: 'Heavy drizzle', 56: 'Freezing drizzle', 57: 'Freezing drizzle',
    61: 'Light rain', 63: 'Rain', 65: 'Heavy rain', 66: 'Freezing rain', 67: 'Freezing rain',
    71: 'Light snow', 73: 'Snow', 75: 'Heavy snow', 77: 'Snow grains',
    80: 'Showers', 81: 'Showers', 82: 'Heavy showers', 85: 'Snow showers', 86: 'Snow showers',
    95: 'Thunderstorm', 96: 'Thunderstorm', 99: 'Thunderstorm'
  };

  var lastError = '';

  function request(url, done) {
    var x = new XMLHttpRequest();
    x.open('GET', url);
    x.timeout = 15000;
    x.onload = function () {
      var data = null;
      try { data = JSON.parse(x.responseText); } catch (e) { data = null; }
      done(x.status === 200 ? data : null, x.status);
    };
    x.onerror = function () { done(null, 'network error'); };
    x.ontimeout = function () { done(null, 'timeout'); };
    x.send();
  }

  // The TV's old browser may reject a modern certificate that its curl accepts, so fall
  // back to plain HTTP. Only a city name or coordinates would travel unencrypted.
  function getJSON(hostAndPath, done) {
    request('https://' + hostAndPath, function (data, status) {
      if (data) { lastError = ''; done(data); return; }
      request('http://' + hostAndPath, function (data2, status2) {
        lastError = data2 ? '' : 'secure: ' + status + ', plain: ' + status2;
        done(data2);
      });
    });
  }

  function lookup(name, done) {
    var path = 'geocoding-api.open-meteo.com/v1/search?count=10&language=en&format=json&name=' + encodeURIComponent(name);
    getJSON(path, function (d) { done(d && d.results ? d.results : d ? [] : null); });
  }

  // The geocoder finds "City, ST" and "City" but not "City st" or "City Statename".
  // Try the comma form, then drop trailing words and use them to rank by state or country.
  function search(name, done) {
    var words = name.replace(/,/g, ' ').split(/\s+/).filter(Boolean);
    var tries = [{ q: name, rest: '' }];
    if (words.length > 1) {
      tries.push({ q: words.slice(0, -1).join(' ') + ', ' + words[words.length - 1], rest: '' });
      for (var n = words.length - 1; n > 0; n--) {
        tries.push({ q: words.slice(0, n).join(' '), rest: words.slice(n).join(' ').toLowerCase() });
      }
    }
    function next(i) {
      if (i >= tries.length) { done([]); return; }
      lookup(tries[i].q, function (found) {
        if (!found) { done(null); return; }
        if (!found.length) { next(i + 1); return; }
        var rest = tries[i].rest;
        var match = found.filter(function (r) { return ((r.admin1 || '') + ' ' + (r.country || '')).toLowerCase().indexOf(rest) !== -1; });
        done((match.length ? match : found).slice(0, 5));
      });
    }
    next(0);
  }

  function fetchNow(loc, unit, done) {
    var path = 'api.open-meteo.com/v1/forecast?latitude=' + loc.lat + '&longitude=' + loc.lon +
      '&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min' +
      '&forecast_days=1&timezone=auto&temperature_unit=' + (unit === 'C' ? 'celsius' : 'fahrenheit');
    getJSON(path, function (d) {
      if (!d || !d.current || !d.daily) { done(null); return; }
      done({
        temp: Math.round(d.current.temperature_2m),
        code: d.current.weather_code,
        high: Math.round(d.daily.temperature_2m_max[0]),
        low: Math.round(d.daily.temperature_2m_min[0]),
        unit: unit,
        at: Date.now()
      });
    });
  }

  function label(code) { return TEXT[code] || ''; }

  return {
    search: search,
    fetchNow: fetchNow,
    label: label,
    lastError: function () { return lastError; }
  };
})();
