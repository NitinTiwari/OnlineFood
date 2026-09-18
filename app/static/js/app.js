// FeastFlow AI - Multi-Agent Food Concierge Client

document.addEventListener("DOMContentLoaded", () => {
    // State
    const state = {
        activeCustomerId: 1,
        activeCustomerName: "Veer Sharma",
        customers: [],
        orders: [],
        products: [],
        chatHistory: []
    };

    // DOM Elements
    const customerSelect = document.getElementById("customerSelect");
    const bannerCustName = document.getElementById("bannerCustName");
    const bannerCustAddress = document.getElementById("bannerCustAddress");
    const bannerActiveOrderBadge = document.getElementById("bannerActiveOrderBadge");
    const chatMessages = document.getElementById("chatMessages");
    const chatForm = document.getElementById("chatForm");
    const queryInput = document.getElementById("queryInput");
    const btnSend = document.getElementById("btnSend");
    const btnResetDb = document.getElementById("btnResetDb");
    const btnRefreshDb = document.getElementById("btnRefreshDb");

    // Inspector Tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const subtabBtns = document.querySelectorAll(".subtab-btn");
    const subtabPanes = document.querySelectorAll(".subtab-pane");

    // Containers
    const ordersTableContainer = document.getElementById("ordersTableContainer");
    const productsTableContainer = document.getElementById("productsTableContainer");
    const customersTableContainer = document.getElementById("customersTableContainer");
    const ordersCount = document.getElementById("ordersCount");
    const productsCount = document.getElementById("productsCount");
    const customersCount = document.getElementById("customersCount");

    // Vector Search Elements
    const vectorSearchInput = document.getElementById("vectorSearchInput");
    const btnVectorSearch = document.getElementById("btnVectorSearch");
    const vFilterVeg = document.getElementById("vFilterVeg");
    const vFilterGf = document.getElementById("vFilterGf");
    const vFilterSpicy = document.getElementById("vFilterSpicy");
    const vCategorySelect = document.getElementById("vCategorySelect");
    const vectorResultsContainer = document.getElementById("vectorResultsContainer");

    // Prompt Chips
    const promptChips = document.querySelectorAll(".prompt-chip");

    // Initialize App
    initApp();

    async function initApp() {
        setupEventListeners();
        await loadCustomers();
        await loadStoreDbData();
        updateActiveCustomerBanner();
    }

    function setupEventListeners() {
        // Customer Picker Change
        customerSelect.addEventListener("change", (e) => {
            state.activeCustomerId = parseInt(e.target.value);
            const found = state.customers.find(c => c.id === state.activeCustomerId);
            if (found) {
                state.activeCustomerName = found.name;
            }
            updateActiveCustomerBanner();
        });

        // Chat Form Submit
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const query = queryInput.value.trim();
            if (!query) return;
            queryInput.value = "";
            await handleSendMessage(query);
        });

        // Quick Prompt Chips
        promptChips.forEach(chip => {
            chip.addEventListener("click", () => {
                const query = chip.getAttribute("data-query");
                if (query) {
                    handleSendMessage(query);
                }
            });
        });

        // Main Tab Switching
        tabBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                tabBtns.forEach(b => b.classList.remove("active"));
                tabPanes.forEach(p => p.classList.remove("active"));
                btn.classList.add("active");
                const targetTab = btn.getAttribute("data-tab");
                const pane = document.getElementById(targetTab);
                if (pane) pane.classList.add("active");
            });
        });

        // Subtab Switching (StoreDB explorer)
        subtabBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                subtabBtns.forEach(b => b.classList.remove("active"));
                subtabPanes.forEach(p => p.classList.remove("active"));
                btn.classList.add("active");
                const targetSubtab = btn.getAttribute("data-subtab");
                const pane = document.getElementById(targetSubtab);
                if (pane) pane.classList.add("active");
            });
        });

        // Refresh StoreDB Button
        if (btnRefreshDb) {
            btnRefreshDb.addEventListener("click", async () => {
                btnRefreshDb.classList.add("spinning");
                await loadStoreDbData();
                btnRefreshDb.classList.remove("spinning");
            });
        }

        // Reset Database Button
        if (btnResetDb) {
            btnResetDb.addEventListener("click", async () => {
                if (confirm("Reset StoreDB and re-index all Vector DB embeddings?")) {
                    try {
                        const res = await fetch("/api/db/reset", { method: "POST" });
                        const data = await res.json();
                        alert(data.message || "Database reset successfully!");
                        await loadCustomers();
                        await loadStoreDbData();
                        updateActiveCustomerBanner();
                    } catch (err) {
                        alert("Failed to reset database: " + err.message);
                    }
                }
            });
        }

        // Vector Search Playground
        if (btnVectorSearch) {
            btnVectorSearch.addEventListener("click", performVectorSearch);
            vectorSearchInput.addEventListener("keypress", (e) => {
                if (e.key === "Enter") performVectorSearch();
            });
        }
    }

    // Load Customers
    async function loadCustomers() {
        try {
            const res = await fetch("/api/customers");
            const data = await res.json();
            state.customers = data.customers || [];
            
            // Populate Dropdown
            customerSelect.innerHTML = "";
            state.customers.forEach(c => {
                const opt = document.createElement("option");
                opt.value = c.id;
                opt.textContent = `${c.name} (${c.total_orders || 0} Orders)`;
                if (c.id === state.activeCustomerId) {
                    opt.selected = true;
                }
                customerSelect.appendChild(opt);
            });

            if (customersCount) customersCount.textContent = state.customers.length;
            renderCustomersTable(state.customers);
        } catch (err) {
            console.error("Error loading customers:", err);
        }
    }

    // Load StoreDB Data (Orders and Products)
    async function loadStoreDbData() {
        try {
            // Load Orders
            const ordersRes = await fetch("/api/orders");
            const ordersData = await ordersRes.json();
            state.orders = ordersData.orders || [];
            if (ordersCount) ordersCount.textContent = state.orders.length;
            renderOrdersTable(state.orders);

            // Load Products
            const productsRes = await fetch("/api/products");
            const productsData = await productsRes.json();
            state.products = productsData.products || [];
            if (productsCount) productsCount.textContent = state.products.length;
            renderProductsTable(state.products);
        } catch (err) {
            console.error("Error loading StoreDB data:", err);
        }
    }

    // Update Customer Banner
    function updateActiveCustomerBanner() {
        const customer = state.customers.find(c => c.id === state.activeCustomerId);
        if (customer) {
            bannerCustName.textContent = customer.name;
            bannerCustAddress.innerHTML = `<i data-lucide="map-pin"></i> ${customer.address}`;
            
            // Find active order for this customer
            const activeOrder = state.orders.find(o => 
                o.customer_id === customer.id && ["Pending", "Preparing", "Out for Delivery"].includes(o.status)
            );

            if (activeOrder) {
                bannerActiveOrderBadge.innerHTML = `<span class="badge-pill pulse">${activeOrder.status} (${activeOrder.order_number})</span>`;
            } else {
                bannerActiveOrderBadge.innerHTML = `<span class="badge-pill" style="background: rgba(255,255,255,0.06); color: var(--text-muted); border-color: var(--border-subtle);">No Active Orders</span>`;
            }
            lucide.createIcons();
        }
    }

    // Handle Sending Message
    async function handleSendMessage(query) {
        // 1. Render User Message
        appendUserMessage(query);
        scrollChatToBottom();

        // 2. Show Typing Indicator
        const typingElem = showTypingIndicator();
        scrollChatToBottom();

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    customer_id: state.activeCustomerId,
                    customer_name: state.activeCustomerName,
                    history: state.chatHistory
                })
            });

            const data = await res.json();
            typingElem.remove();

            if (!res.ok) {
                appendErrorMessage(data.detail || "An error occurred while processing your request.");
                return;
            }

            // 3. Render Assistant Response
            appendBotResponse(data);
            scrollChatToBottom();

            // Save history
            state.chatHistory.push({ role: "user", content: query });
            state.chatHistory.push({ role: "assistant", content: data.response });

            // Refresh StoreDB tables in case status changed
            loadStoreDbData();
            updateActiveCustomerBanner();

        } catch (err) {
            typingElem.remove();
            appendErrorMessage("Connection error: Could not reach the Multi-Agent server.");
            console.error(err);
        }
    }

    // Append User Message
    function appendUserMessage(text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message-wrapper user-message";
        msgDiv.innerHTML = `
            <div class="user-avatar">
                <i data-lucide="user"></i>
            </div>
            <div class="message-bubble">
                <div class="message-body">
                    <p>${escapeHtml(text)}</p>
                </div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        lucide.createIcons();
    }

    // Show Typing Indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.className = "message-wrapper bot-message";
        typingDiv.id = "activeTyping";
        typingDiv.innerHTML = `
            <div class="agent-avatar supervisor-avatar">
                <i data-lucide="git-branch"></i>
            </div>
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        lucide.createIcons();
        return typingDiv;
    }

    // Append Assistant Response
    function appendBotResponse(data) {
        const { response, active_agent, agent_trace, order_data, menu_matches } = data;

        // Choose avatar style based on active agent
        let avatarClass = "supervisor-avatar";
        let avatarIcon = "bot";
        let tagClass = "supervisor-tag";

        if (active_agent.includes("Order")) {
            avatarClass = "order-avatar";
            avatarIcon = "package-check";
            tagClass = "order-tag";
        } else if (active_agent.includes("Menu")) {
            avatarClass = "menu-avatar";
            avatarIcon = "sparkles";
            tagClass = "menu-tag";
        } else if (active_agent.includes("Support")) {
            avatarClass = "support-avatar";
            avatarIcon = "help-circle";
            tagClass = "support-tag";
        }

        const msgDiv = document.createElement("div");
        msgDiv.className = "message-wrapper bot-message";

        // Build Trace Steps HTML
        let traceHtml = "";
        if (agent_trace && agent_trace.length > 0) {
            const stepsHtml = agent_trace.map(t => `
                <div class="trace-step-item">
                    <div class="step-agent-title">🤖 ${escapeHtml(t.agent || "Agent")}</div>
                    <div class="step-thought">💭 ${escapeHtml(t.thought || "")}</div>
                    ${t.tool_called ? `<div class="step-tool">⚡ Tool Executed: <code>${escapeHtml(t.tool_called)}</code></div>` : ""}
                </div>
            `).join("");

            traceHtml = `
                <details class="trace-accordion">
                    <summary class="trace-summary">
                        <i data-lucide="activity"></i> Multi-Agent Execution Trace (${agent_trace.length} steps)
                    </summary>
                    <div class="trace-content">
                        ${stepsHtml}
                    </div>
                </details>
            `;
        }

        // Parse Markdown Response
        const parsedMarkdown = marked.parse(response || "");

        // Build Order Tracker Card if order data present
        let orderCardHtml = "";
        if (order_data) {
            orderCardHtml = createOrderTrackerCardHtml(order_data);
        }

        // Build Food Recommendation Cards if menu matches present
        let foodCardsHtml = "";
        if (menu_matches && menu_matches.length > 0) {
            foodCardsHtml = createFoodRecommendationCardsHtml(menu_matches);
        }

        msgDiv.innerHTML = `
            <div class="agent-avatar ${avatarClass}">
                <i data-lucide="${avatarIcon}"></i>
            </div>
            <div class="message-bubble">
                <div class="message-meta">
                    <span class="agent-tag ${tagClass}">
                        <i data-lucide="shield-check"></i> ${escapeHtml(active_agent)}
                    </span>
                    <span class="timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                ${traceHtml}
                <div class="message-body">
                    ${parsedMarkdown}
                </div>
                ${orderCardHtml}
                ${foodCardsHtml}
            </div>
        `;

        chatMessages.appendChild(msgDiv);
        lucide.createIcons();

        // Attach event listeners for dynamic "Ask about this" buttons on food cards
        msgDiv.querySelectorAll(".btn-ask-food").forEach(btn => {
            btn.addEventListener("click", () => {
                const itemName = btn.getAttribute("data-item-name");
                if (itemName) {
                    handleSendMessage(`Tell me more about ${itemName} and ingredients`);
                }
            });
        });
    }

    // Create Order Tracker HTML
    function createOrderTrackerCardHtml(order) {
        const num = order.order_number || "N/A";
        const status = order.status || "Pending";
        const total = (order.total_amount || 0).toFixed(2);
        const eta = order.estimated_delivery_time || "Estimating...";
        const addr = order.delivery_address || "Address on file";

        const stages = ["Pending", "Preparing", "Out for Delivery", "Delivered"];
        const currentIdx = stages.indexOf(status);

        const statusClass = `status-${status.toLowerCase().replace(/\s+/g, '-')}`;

        let progressPercent = 0;
        if (currentIdx === 0) progressPercent = 10;
        else if (currentIdx === 1) progressPercent = 45;
        else if (currentIdx === 2) progressPercent = 80;
        else if (currentIdx === 3) progressPercent = 100;

        const nodesHtml = stages.map((stage, idx) => {
            let nodeClass = "";
            if (idx < currentIdx) nodeClass = "completed";
            else if (idx === currentIdx) nodeClass = "active";

            const icons = ["⏳", "🍳", "🛵", "✅"];
            return `
                <div class="progress-node ${nodeClass}">
                    <div class="node-dot">${icons[idx]}</div>
                    <span class="node-label">${stage}</span>
                </div>
            `;
        }).join("");

        return `
            <div class="order-tracker-card">
                <div class="tracker-header">
                    <div class="tracker-order-id">
                        <i data-lucide="package"></i> Order ${escapeHtml(num)}
                    </div>
                    <div class="tracker-status-pill ${statusClass}">${escapeHtml(status)}</div>
                </div>

                <div class="tracker-progress-bar">
                    <div class="progress-track">
                        <div class="progress-fill" style="width: ${progressPercent}%;"></div>
                    </div>
                    ${nodesHtml}
                </div>

                <div class="tracker-details-grid">
                    <div class="tracker-detail-item">
                        <span class="detail-label">Estimated Delivery / ETA</span>
                        <span class="detail-val">${escapeHtml(eta)}</span>
                    </div>
                    <div class="tracker-detail-item">
                        <span class="detail-label">Total Amount</span>
                        <span class="detail-val" style="color: var(--accent-orange);">$${total}</span>
                    </div>
                    <div class="tracker-detail-item" style="grid-column: span 2;">
                        <span class="detail-label">Delivery Address</span>
                        <span class="detail-val">${escapeHtml(addr)}</span>
                    </div>
                </div>
            </div>
        `;
    }

    // Create Food Cards HTML
    function createFoodRecommendationCardsHtml(products) {
        const cardsHtml = products.slice(0, 3).map(p => {
            const name = p.name || "Dish";
            const price = (p.price || 0).toFixed(2);
            const cat = p.category || "Menu";
            const desc = p.description || "";
            const img = p.image_url || "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500";

            let tagsHtml = "";
            if (p.is_vegetarian) tagsHtml += `<span class="food-tag tag-veg">🌱 Veg</span>`;
            if (p.is_gluten_free) tagsHtml += `<span class="food-tag tag-gf">🌾 GF</span>`;
            if (p.is_spicy) tagsHtml += `<span class="food-tag tag-spicy">🌶️ Spicy</span>`;

            return `
                <div class="food-card">
                    <div class="food-img-container">
                        <img src="${img}" alt="${escapeHtml(name)}" class="food-img" onerror="this.src='https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500'" />
                        <span class="food-category-badge">${escapeHtml(cat)}</span>
                    </div>
                    <div class="food-info">
                        <div>
                            <div class="food-title">${escapeHtml(name)}</div>
                            <div class="food-desc">${escapeHtml(desc)}</div>
                            <div class="food-tags">${tagsHtml}</div>
                        </div>
                        <div class="food-footer">
                            <span class="food-price">$${price}</span>
                            <button class="btn-ask-food" data-item-name="${escapeHtml(name)}">
                                <i data-lucide="info"></i> Details
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join("");

        return `
            <div class="food-recommendations-grid">
                ${cardsHtml}
            </div>
        `;
    }

    // Append Error Message
    function appendErrorMessage(text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message-wrapper bot-message";
        msgDiv.innerHTML = `
            <div class="agent-avatar" style="background: #ef4444; color: white;">
                <i data-lucide="alert-triangle"></i>
            </div>
            <div class="message-bubble" style="border-color: #ef4444;">
                <div class="message-body" style="color: #fca5a5;">
                    <p><strong>Error:</strong> ${escapeHtml(text)}</p>
                </div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        lucide.createIcons();
    }

    // Render StoreDB Orders Table
    function renderOrdersTable(orders) {
        if (!orders || orders.length === 0) {
            ordersTableContainer.innerHTML = `<div class="empty-state"><p>No orders found in StoreDB.</p></div>`;
            return;
        }

        const rowsHtml = orders.map(o => {
            const statusClass = `status-${o.status.toLowerCase().replace(/\s+/g, '-')}`;
            const itemsSummary = (o.items || []).map(i => `${i.quantity}x ${i.product_name}`).join(", ");
            return `
                <tr>
                    <td><strong>${escapeHtml(o.order_number)}</strong></td>
                    <td>${escapeHtml(o.customer_name || "Customer #" + o.customer_id)}</td>
                    <td><span class="tracker-status-pill ${statusClass}">${escapeHtml(o.status)}</span></td>
                    <td>$${(o.total_amount || 0).toFixed(2)}</td>
                    <td title="${escapeHtml(itemsSummary)}" style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(itemsSummary)}</td>
                    <td style="font-size: 0.72rem; color: var(--text-muted);">${escapeHtml(o.created_at || "")}</td>
                </tr>
            `;
        }).join("");

        ordersTableContainer.innerHTML = `
            <table class="db-table">
                <thead>
                    <tr>
                        <th>Order #</th>
                        <th>Customer</th>
                        <th>Status</th>
                        <th>Total</th>
                        <th>Items</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        `;
    }

    // Render StoreDB Products Table
    function renderProductsTable(products) {
        if (!products || products.length === 0) {
            productsTableContainer.innerHTML = `<div class="empty-state"><p>No products found in StoreDB.</p></div>`;
            return;
        }

        const rowsHtml = products.map(p => {
            let tags = [];
            if (p.is_vegetarian) tags.push("Veg");
            if (p.is_gluten_free) tags.push("GF");
            if (p.is_spicy) tags.push("Spicy");
            const tagsStr = tags.join(", ") || "-";

            return `
                <tr>
                    <td><strong>${escapeHtml(p.name)}</strong></td>
                    <td><span class="food-category-badge" style="position:static; display:inline-block;">${escapeHtml(p.category)}</span></td>
                    <td style="color: var(--accent-orange); font-weight: 600;">$${(p.price || 0).toFixed(2)}</td>
                    <td>${p.calories || 'N/A'} kcal</td>
                    <td>${tagsStr}</td>
                    <td><span class="sim-score-badge">In Stock</span></td>
                </tr>
            `;
        }).join("");

        productsTableContainer.innerHTML = `
            <table class="db-table">
                <thead>
                    <tr>
                        <th>Dish Name</th>
                        <th>Category</th>
                        <th>Price</th>
                        <th>Calories</th>
                        <th>Diet</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        `;
    }

    // Render StoreDB Customers Table
    function renderCustomersTable(customers) {
        if (!customers || customers.length === 0) {
            customersTableContainer.innerHTML = `<div class="empty-state"><p>No customers found in StoreDB.</p></div>`;
            return;
        }

        const rowsHtml = customers.map(c => `
            <tr>
                <td><strong>#${c.id} ${escapeHtml(c.name)}</strong></td>
                <td>${escapeHtml(c.email)}</td>
                <td>${escapeHtml(c.phone)}</td>
                <td title="${escapeHtml(c.address)}" style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(c.address)}</td>
                <td><strong>${c.total_orders || 0}</strong></td>
            </tr>
        `).join("");

        customersTableContainer.innerHTML = `
            <table class="db-table">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Address</th>
                        <th>Orders</th>
                    </tr>
                </thead>
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        `;
    }

    // Perform Vector Search
    async function performVectorSearch() {
        const query = vectorSearchInput.value.trim();
        if (!query) return;

        const category = vCategorySelect.value;
        const isVeg = vFilterVeg.checked;
        const isGf = vFilterGf.checked;
        const isSpicy = vFilterSpicy.checked;

        vectorResultsContainer.innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2"></i> Searching Vector DB embeddings...</div>`;
        lucide.createIcons();

        try {
            const params = new URLSearchParams({ query });
            if (category) params.append("category", category);
            if (isVeg) params.append("is_vegetarian", "true");
            if (isGf) params.append("is_gluten_free", "true");
            if (isSpicy) params.append("is_spicy", "true");

            const res = await fetch(`/api/menu/search?${params.toString()}`);
            const data = await res.json();
            const results = data.results || [];

            if (results.length === 0) {
                vectorResultsContainer.innerHTML = `
                    <div class="empty-state">
                        <i data-lucide="alert-circle"></i>
                        <p>No menu items matched your vector query and filters.</p>
                    </div>
                `;
                lucide.createIcons();
                return;
            }

            const resultsHtml = results.map(r => {
                const p = r.product;
                const score = (r.similarity_score * 100).toFixed(1);
                return `
                    <div class="vector-result-item">
                        <div class="vector-res-header">
                            <span class="vector-res-title">${escapeHtml(p.name)}</span>
                            <span class="sim-score-badge">Match: ${score}%</span>
                        </div>
                        <p style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 6px;">${escapeHtml(p.description)}</p>
                        <div style="display: flex; justify-content: space-between; font-size: 0.74rem; color: var(--text-muted);">
                            <span>Category: <strong>${escapeHtml(p.category)}</strong></span>
                            <span style="color: var(--accent-orange); font-weight: 600;">$${(p.price || 0).toFixed(2)}</span>
                        </div>
                    </div>
                `;
            }).join("");

            vectorResultsContainer.innerHTML = resultsHtml;
            lucide.createIcons();

        } catch (err) {
            vectorResultsContainer.innerHTML = `<div class="empty-state"><p>Vector search error: ${err.message}</p></div>`;
        }
    }

    // Utility: Scroll Chat
    function scrollChatToBottom() {
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 50);
    }

    // Utility: Escape HTML
    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
