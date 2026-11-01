/* The API client.  Builds Api.group.name(args) for every entry in routes.js
   and sends it through a transport:

     HttpTransport  - fetch() against server.py (the real application)
     MockTransport  - calls the sample-data functions in mock.js (browser preview, tests)

   Screens never know which transport is in use, and never build URLs or
   call Python methods by name. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) { module.exports = factory(require("./routes.js")); }
  else { root.ApiClient = factory(root.API_ROUTES); }
})(typeof self !== "undefined" ? self : this, function (ROUTES) {
  "use strict";

  function fillPath(path, args) {
    var used = {};
    var filled = path.replace(/\{(\w+)\}/g, function (_, name) { used[name] = true; return encodeURIComponent(args[name] === undefined || args[name] === null ? "" : args[name]); });
    return { path: filled, used: used };
  }

  var globalScope = typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this);

  function HttpTransport(baseUrl, token, fetchImpl) {
    this.baseUrl = baseUrl || "";
    this.token = token || "";
    this.fetch = fetchImpl || (typeof globalScope.fetch === "function" ? globalScope.fetch.bind(globalScope) : null);
    if (!this.fetch) { throw new Error("This browser has no fetch(); Iceberg needs a current webview runtime."); }
  }
  HttpTransport.prototype.call = function (route, args) {
    var target = fillPath(route.path, args), url = this.baseUrl + target.path, options = { method: route.method, headers: { "X-Iceberg-Token": this.token } };
    var rest = {};
    route.params.forEach(function (name) { if (!target.used[name] && args[name] !== undefined) { rest[name] = args[name]; } });
    if (route.method === "GET") {
      var query = Object.keys(rest).map(function (k) { return encodeURIComponent(k) + "=" + encodeURIComponent(rest[k] === null ? "" : rest[k]); }).join("&");
      if (query) { url += "?" + query; }
    } else {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(rest);
    }
    return this.fetch(url, options).then(function (response) {
      return response.json().catch(function () { return { ok: false, message: "The server returned an unreadable response (" + response.status + ").", errors: [] }; });
    }).catch(function (error) {
      return { ok: false, message: "Iceberg's local service did not respond: " + error, errors: [] };
    });
  };

  function MockTransport(mock) { this.mock = mock; }
  MockTransport.prototype.call = function (route, args) {
    var fn = this.mock[route.handler];
    if (typeof fn !== "function") { return Promise.resolve({ ok: false, message: "Mock has no handler " + route.handler, errors: [] }); }
    return Promise.resolve(fn.apply(this.mock, route.params.map(function (name) { return args[name]; })));
  };

  function build(transport) {
    var api = { _transport: transport, _routes: {} };
    Object.keys(ROUTES).forEach(function (key) {
      var parts = key.split("."), group = parts[0], name = parts[1], spec = ROUTES[key];
      var route = { method: spec[0], path: spec[1], handler: spec[2], params: spec[3] || [] };
      api._routes[key] = route;
      api[group] = api[group] || {};
      api[group][name] = function (args) { return transport.call(route, args || {}); };
    });
    api.call = function (key, args) { return transport.call(api._routes[key], args || {}); };
    return api;
  }

  function tokenFromLocation(location) {
    var match = /[?&]token=([^&]+)/.exec((location && location.search) || "");
    return match ? decodeURIComponent(match[1]) : "";
  }

  return { build: build, HttpTransport: HttpTransport, MockTransport: MockTransport, fillPath: fillPath, tokenFromLocation: tokenFromLocation, ROUTES: ROUTES };
});
