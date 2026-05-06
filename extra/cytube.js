/**
 * cytube-queue-buttons.js
 *
 * Injects "Copy Manifest URL" and "Queue Next in CyTube" buttons into the
 * dropsugar media view. Include this file in the page template — no browser
 * extension required.
 *
 * kryten-api-gate must have `allowed_origins: ["https://www.dropsugar.co"]`
 * in config.json for the cross-origin fetch to succeed.
 */

(function () {
    'use strict';

    // -----------------------------------------------------------------------
    // Config
    // -----------------------------------------------------------------------
    const DEBUG        = false;
    const KRYTEN_BASE  = 'http://127.0.0.1:24444/api/v1';
    const KRYTEN_TOKEN = 'your-api-key';   // value from api_keys in kryten-api-gate config.json
    const QUEUE_TEMP   = false;            // true = item removed from playlist after playback

    // -----------------------------------------------------------------------
    // Logging
    // -----------------------------------------------------------------------
    function log(text) {
        if (!DEBUG) return;
        if (typeof text === 'object') text = JSON.stringify(text);
        console.log('[cytube-queue] ' + new Date().toISOString() + ' ' + text);
    }

    // -----------------------------------------------------------------------
    // Clipboard
    // -----------------------------------------------------------------------
    function copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text)
                .then(function () { log('copied: ' + text); })
                .catch(function () { fallbackCopy(text); });
        } else {
            fallbackCopy(text);
        }
    }

    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        try { document.execCommand('copy'); } catch (e) { log('fallback copy failed: ' + e); }
        document.body.removeChild(ta);
    }

    // -----------------------------------------------------------------------
    // Manifest URL — derived from the current page URL (?m=<mediaId>)
    // -----------------------------------------------------------------------
    function getManifestURL() {
        var mediaId = new URLSearchParams(window.location.search).get('m');
        if (!mediaId) { log('no ?m= param in URL'); return null; }
        return 'https://www.dropsugar.co/api/v1/media/cytube/' + mediaId + '.json?format=json';
    }

    // -----------------------------------------------------------------------
    // Button helpers
    // -----------------------------------------------------------------------
    var BTN_STYLE = 'margin:5px;padding:5px 10px;background:#009933;color:#efefef;' +
                   'cursor:pointer;border:none;border-radius:3px;font-size:13px;';

    function makeButton(container, id, label, onClick) {
        var btn = document.createElement('button');
        btn.id = id;
        btn.textContent = label;
        btn.style.cssText = BTN_STYLE;
        var wrapper = document.createElement('div');
        wrapper.appendChild(btn);
        container.appendChild(wrapper);
        btn.addEventListener('click', function (e) { e.preventDefault(); onClick(btn); });
        return btn;
    }

    function flash(btn, label, ms) {
        ms = ms || 2000;
        var orig = btn.textContent;
        btn.textContent = label;
        btn.disabled = true;
        setTimeout(function () { btn.textContent = orig; btn.disabled = false; }, ms);
    }

    // -----------------------------------------------------------------------
    // Queue via kryten-api-gate (plain fetch — CORS handled server-side)
    // -----------------------------------------------------------------------
    function queueNext(manifestUrl, btn) {
        log('queueNext: ' + manifestUrl);
        btn.textContent = 'Queuing\u2026';
        btn.disabled = true;

        fetch(KRYTEN_BASE + '/playlist/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + KRYTEN_TOKEN,
            },
            body: JSON.stringify({ type: 'cm', id: manifestUrl, position: 'next', temp: QUEUE_TEMP }),
        })
        .then(function (res) {
            return res.json().then(function (data) {
                log('response ' + res.status + ': ' + JSON.stringify(data));
                if (res.ok && data.success) {
                    flash(btn, '\u2713 Queued!');
                } else {
                    flash(btn, '\u2717 ' + (data.detail || 'Failed'), 3500);
                }
            });
        })
        .catch(function (err) {
            log('fetch error: ' + err);
            flash(btn, '\u2717 Network error', 3000);
        });
    }

    // -----------------------------------------------------------------------
    // Wait for React to render the target container, then inject buttons
    // -----------------------------------------------------------------------
    var TARGET = '#page-media > div > div.cf.viewer-section.viewer-wide > ' +
                 'div.viewer-section-nested > div.viewer-info > div > ' +
                 'div.media-title-banner > div > div.media-actions > div:nth-child(1)';

    function waitForElm(selector) {
        return new Promise(function (resolve) {
            var el = document.querySelector(selector);
            if (el) return resolve(el);
            var obs = new MutationObserver(function () {
                var el = document.querySelector(selector);
                if (el) { obs.disconnect(); resolve(el); }
            });
            obs.observe(document.body, { childList: true, subtree: true });
        });
    }

    waitForElm(TARGET).then(function (container) {
        var manifestUrl = getManifestURL();
        if (!manifestUrl) return;

        makeButton(container, 'kryten-copy-url', '\uD83D\uDCCB Copy Manifest URL', function (btn) {
            copyToClipboard(manifestUrl);
            flash(btn, '\u2713 Copied!');
        });

        makeButton(container, 'kryten-queue-next', '\u25B6 Queue Next in CyTube', function (btn) {
            queueNext(manifestUrl, btn);
        });

        log('buttons injected');
    });

}());
