/* =========================================================
   VOYAGEAI JAVASCRIPT
========================================================= */


/* =========================================================
   HOME MODAL
========================================================= */

function openInfoModal(type) {

    const modal =
        document.getElementById("infoModal");

    if (!modal) {
        return;
    }


    const about =
        document.getElementById("modalAbout");

    const algorithms =
        document.getElementById("modalAlgorithms");

    const creator =
        document.getElementById("modalCreator");


    if (about) {
        about.classList.add("hidden");
    }

    if (algorithms) {
        algorithms.classList.add("hidden");
    }

    if (creator) {
        creator.classList.add("hidden");
    }


    if (type === "about" && about) {
        about.classList.remove("hidden");
    }


    if (
        type === "algorithms"
        &&
        algorithms
    ) {
        algorithms.classList.remove("hidden");
    }


    if (
        type === "creator"
        &&
        creator
    ) {
        creator.classList.remove("hidden");
    }


    modal.classList.add("show");
}


function closeInfoModal() {

    const modal =
        document.getElementById("infoModal");


    if (modal) {

        modal.classList.remove(
            "show"
        );

    }

}


document.addEventListener(
    "click",
    function(event) {

        const modal =
            document.getElementById(
                "infoModal"
            );


        if (!modal) {
            return;
        }


        if (
            modal.classList.contains("show")
            &&
            event.target === modal
        ) {

            modal.classList.remove(
                "show"
            );

        }

    }
);


document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Escape"
        ) {

            closeInfoModal();

        }

    }
);


/* =========================================================
   RESULT PAGE TABS
========================================================= */

function showResultTab(
    tabName,
    button
) {

    const panels =
        document.querySelectorAll(
            ".workspace-panel"
        );


    const tabs =
        document.querySelectorAll(
            ".workspace-tab"
        );


    panels.forEach(
        function(panel) {

            panel.classList.remove(
                "active"
            );

        }
    );


    tabs.forEach(
        function(tab) {

            tab.classList.remove(
                "active"
            );

        }
    );


    const panelIds = {

        itinerary:
            "resultItinerary",

        transport:
            "resultTransport",

        nearby:
            "resultNearby",

        map:
            "resultMap"

    };


    const selectedPanel =
        document.getElementById(
            panelIds[tabName]
        );


    if (selectedPanel) {

        selectedPanel.classList.add(
            "active"
        );

    }


    if (button) {

        button.classList.add(
            "active"
        );

    }

}


/* =========================================================
   NEARBY FOOD / HOTELS
========================================================= */

function showNearbyTab(
    type,
    button
) {

    const food =
        document.getElementById(
            "nearbyFood"
        );


    const hotels =
        document.getElementById(
            "nearbyHotels"
        );


    const buttons =
        document.querySelectorAll(
            ".nearby-switch-button"
        );


    if (food) {

        food.classList.remove(
            "active"
        );

    }


    if (hotels) {

        hotels.classList.remove(
            "active"
        );

    }


    buttons.forEach(
        function(item) {

            item.classList.remove(
                "active"
            );

        }
    );


    if (
        type === "food"
        &&
        food
    ) {

        food.classList.add(
            "active"
        );

    }


    if (
        type === "hotels"
        &&
        hotels
    ) {

        hotels.classList.add(
            "active"
        );

    }


    if (button) {

        button.classList.add(
            "active"
        );

    }

}


/* =========================================================
   CHATBOT
   KEPT FUNCTIONAL
========================================================= */

async function sendMessage() {

    const input =
        document.getElementById(
            "messageInput"
        );


    const chat =
        document.getElementById(
            "chatMessages"
        );


    if (!input || !chat) {
        return;
    }


    const message =
        input.value.trim();


    if (!message) {
        return;
    }


    addMessage(
        message,
        "user"
    );


    input.value = "";


    const thinking =
        addMessage(
            "🤖 Thinking...",
            "bot"
        );


    try {

        const response =
            await fetch(
                "/chat",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body: JSON.stringify({

                        message:
                            message

                    })

                }
            );


        if (!response.ok) {

            throw new Error(
                "Chat request failed"
            );

        }


        const data =
            await response.json();


        if (thinking) {

            thinking.remove();

        }


        addMessage(

            data.reply
            ||
            "I couldn't generate a response.",

            "bot"

        );


        if (
            data.type === "destination"
            &&
            Array.isArray(
                data.places
            )
        ) {

            data.places.forEach(
                function(place) {

                    addPlaceCard(
                        place
                    );

                }
            );

        }


    } catch (error) {


        if (thinking) {

            thinking.remove();

        }


        addMessage(

            "❌ I couldn't connect right now. Please try again.",

            "bot"

        );


        console.error(
            error
        );

    }

}


/* =========================================================
   ADD CHAT MESSAGE
========================================================= */

function addMessage(
    message,
    type
) {

    const chat =
        document.getElementById(
            "chatMessages"
        );


    if (!chat) {
        return null;
    }


    const div =
        document.createElement(
            "div"
        );


    if (type === "user") {

        div.className =
            "user-message";


        div.textContent =
            message;

    }

    else {

        div.className =
            "bot-message";


        div.innerHTML = `

            <div class="bot-avatar">
                ✦
            </div>

            <div class="bot-bubble"></div>

        `;


        const bubble =
            div.querySelector(
                ".bot-bubble"
            );


        if (bubble) {

            bubble.textContent =
                message;

        }

    }


    chat.appendChild(
        div
    );


    chat.scrollTop =
        chat.scrollHeight;


    return div;

}


/* =========================================================
   AI PLACE CARD
========================================================= */

function addPlaceCard(
    place
) {

    const chat =
        document.getElementById(
            "chatMessages"
        );


    if (!chat) {
        return;
    }


    const card =
        document.createElement(
            "div"
        );


    card.className =
        "ai-place-card";


    const lat =
        Number(
            place.lat
        );


    const lon =
        Number(
            place.lon
        );


    const locationURL =
        "https://www.google.com/maps/search/?api=1&query="
        +
        encodeURIComponent(
            lat + "," + lon
        );


    const directionURL =
        "https://www.google.com/maps/dir/?api=1&destination="
        +
        encodeURIComponent(
            lat + "," + lon
        );


    const name =
        escapeHTML(
            place.name
            ||
            "Place"
        );


    const description =
        escapeHTML(
            place.description
            ||
            "Interesting place to explore."
        );


    const distance =
        place.distance
        !== undefined
            ? place.distance
            : "-";


    let tags = "";


    if (
        Array.isArray(
            place.tags
        )
    ) {

        tags =
            escapeHTML(
                place.tags.join(
                    " • "
                )
            );

    }


    let score = "";


    if (
        place.ai_score
        !== undefined
    ) {

        score =
            " · 🧠 AI Score: "
            +
            escapeHTML(
                place.ai_score
            );

    }


    card.innerHTML = `

        <div class="ai-place-icon">
            📍
        </div>

        <div class="ai-place-content">

            <strong>
                ${name}
            </strong>

            <p>
                ${description}
            </p>

            <small>

                📏 ${distance} km

                ${score}

                ${
                    tags
                    ? "<br>✦ " + tags
                    : ""
                }

                <br><br>

                <a
                    href="${locationURL}"
                    target="_blank"
                    rel="noopener noreferrer"
                    style="
                        color:#5b50e8;
                        font-weight:800;
                        text-decoration:none;
                    "
                >
                    📍 Location
                </a>

                &nbsp;&nbsp;

                <a
                    href="${directionURL}"
                    target="_blank"
                    rel="noopener noreferrer"
                    style="
                        color:#5b50e8;
                        font-weight:800;
                        text-decoration:none;
                    "
                >
                    🧭 Directions
                </a>

            </small>

        </div>

    `;


    chat.appendChild(
        card
    );


    chat.scrollTop =
        chat.scrollHeight;

}


/* =========================================================
   QUICK QUESTIONS
========================================================= */

function quickMessage(
    message
) {

    const input =
        document.getElementById(
            "messageInput"
        );


    if (!input) {
        return;
    }


    input.value =
        message;


    sendMessage();

}


/* =========================================================
   ENTER TO SEND
========================================================= */

function handleEnter(
    event
) {

    if (
        event.key === "Enter"
    ) {

        event.preventDefault();

        sendMessage();

    }

}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHTML(
    value
) {

    const element =
        document.createElement(
            "div"
        );


    element.textContent =
        String(value);


    return element.innerHTML;

}