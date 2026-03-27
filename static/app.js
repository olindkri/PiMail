(function () {
    const emailsEl = document.getElementById("emails");
    const clockEl = document.getElementById("clock");
    const statusEl = document.getElementById("status");
    const countEl = document.getElementById("mail-count");
    const lastCheckEl = document.getElementById("last-check");

    function updateClock() {
        const now = new Date();
        const h = String(now.getHours()).padStart(2, "0");
        const m = String(now.getMinutes()).padStart(2, "0");
        clockEl.textContent = h + ":" + m;
    }

    function renderEmails(emails) {
        emailsEl.innerHTML = "";

        if (!emails || emails.length === 0) {
            emailsEl.innerHTML = '<div class="no-mail">[ NO MESSAGES ]</div>';
            countEl.textContent = "0 messages";
            return;
        }

        // Render all cards
        const cards = [];
        for (const em of emails) {
            const card = document.createElement("div");
            card.className = "mail-card" + (em.verification_code ? " has-code" : "");

            let html = '<div class="mail-row">';
            html += '<span class="mail-sender">' + escapeHtml(em.sender) + "</span>";
            html += '<span class="mail-time">' + escapeHtml(em.time_ago) + "</span>";
            html += "</div>";
            html += '<div class="mail-summary">' + escapeHtml(em.summary) + "</div>";

            if (em.verification_code) {
                html +=
                    '<div class="mail-code">*** CODE: ' +
                    escapeHtml(em.verification_code) +
                    " ***</div>";
            }

            card.innerHTML = html;
            emailsEl.appendChild(card);
            cards.push(card);
        }

        countEl.textContent = emails.length + " message" + (emails.length !== 1 ? "s" : "");

        // Auto-fit: remove last cards until no overflow
        autoFit(cards);
    }

    function autoFit(cards) {
        // The emails container must not overflow the screen area
        const screen = document.getElementById("screen");
        const maxHeight = screen.clientHeight
            - document.getElementById("header").offsetHeight
            - document.getElementById("footer").offsetHeight
            - 16; // padding/gaps

        while (cards.length > 0 && emailsEl.scrollHeight > maxHeight) {
            const last = cards.pop();
            last.remove();
        }

        // Update count to reflect visible cards
        countEl.textContent = cards.length + " message" + (cards.length !== 1 ? "s" : "");
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function fetchEmails() {
        fetch("/api/emails")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                renderEmails(data.emails);

                if (data.error) {
                    statusEl.textContent = "ERR";
                    statusEl.className = "err";
                } else {
                    statusEl.textContent = "OK";
                    statusEl.className = "ok";
                }

                if (data.last_check) {
                    const d = new Date(data.last_check);
                    const h = String(d.getHours()).padStart(2, "0");
                    const m = String(d.getMinutes()).padStart(2, "0");
                    lastCheckEl.textContent = "last check " + h + ":" + m;
                }
            })
            .catch(function () {
                statusEl.textContent = "ERR";
                statusEl.className = "err";
            });
    }

    // === DRAG TO MOVE ===
    (function () {
        var win = document.getElementById("window");
        var titlebar = document.getElementById("titlebar");
        var offsetX = 0, offsetY = 0, dragging = false;

        function onStart(e) {
            // Don't drag if clicking resize handle area (bottom-right 16px)
            var rect = win.getBoundingClientRect();
            var clientX = e.touches ? e.touches[0].clientX : e.clientX;
            var clientY = e.touches ? e.touches[0].clientY : e.clientY;
            if (clientX > rect.right - 16 && clientY > rect.bottom - 16) return;

            dragging = true;
            // Switch from centered to absolute positioning on first drag
            if (win.style.position !== "absolute") {
                var r = win.getBoundingClientRect();
                win.style.position = "absolute";
                win.style.left = r.left + "px";
                win.style.top = r.top + "px";
            }
            offsetX = clientX - win.offsetLeft;
            offsetY = clientY - win.offsetTop;
            e.preventDefault();
        }

        function onMove(e) {
            if (!dragging) return;
            var clientX = e.touches ? e.touches[0].clientX : e.clientX;
            var clientY = e.touches ? e.touches[0].clientY : e.clientY;
            win.style.left = (clientX - offsetX) + "px";
            win.style.top = (clientY - offsetY) + "px";
            e.preventDefault();
        }

        function onEnd() {
            dragging = false;
        }

        titlebar.addEventListener("mousedown", onStart);
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onEnd);

        titlebar.addEventListener("touchstart", onStart, { passive: false });
        document.addEventListener("touchmove", onMove, { passive: false });
        document.addEventListener("touchend", onEnd);
    })();

    // Re-fit emails when the window is resized
    var resizeTimer;
    var resizeObserver = new ResizeObserver(function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function () {
            // Re-render with last known data to re-fit
            fetchEmails();
        }, 150);
    });
    resizeObserver.observe(document.getElementById("window"));

    // Initial load
    updateClock();
    fetchEmails();

    // Poll every 30 seconds
    setInterval(fetchEmails, 30000);
    // Update clock every 30 seconds
    setInterval(updateClock, 30000);
})();
