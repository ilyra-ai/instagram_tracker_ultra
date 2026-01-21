// Instagram Activity Tracker 2025 - JavaScript Corrigido
// Conecta interface com API e exibe resultados adequadamente

class InstagramTracker {
  constructor() {
    this.apiBase = "/api/instagram";
    this.isTracking = false;
    this.currentResults = null;

    this.init();
  }

  init() {
    this.bindEvents();
    this.checkSystemStatus();
    this.setupTabs();
  }

  bindEvents() {
    // Form submission
    document.getElementById("trackingForm").addEventListener("submit", (e) => {
      e.preventDefault();
      this.startTracking();
    });

    // Clear button
    document.getElementById("clearBtn").addEventListener("click", () => {
      this.clearForm();
    });

    // Stop button
    document.getElementById("stopBtn").addEventListener("click", () => {
      this.stopTracking();
    });

    // Tab switching
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const tabName = e.target.closest(".tab-btn").dataset.tab;
        this.switchTab(tabName);
      });
    });
  }

  async checkSystemStatus() {
    try {
      this.updateStatus("Verificando sistema...", "checking");

      const response = await fetch(`${this.apiBase}/test`);
      const data = await response.json();

      if (data.success) {
        this.updateStatus("Sistema funcionando", "online");
        this.showSystemStatus(data, true);
      } else {
        this.updateStatus("Sistema com problemas", "error");
        this.showSystemStatus(data, false);
      }
    } catch (error) {
      this.updateStatus("Sistema offline", "error");
      this.showSystemStatus({ message: error.message }, false);
    }
  }

  updateStatus(text, status) {
    const indicator = document.getElementById("statusIndicator");
    const statusText = indicator.querySelector(".status-text");
    const statusDot = indicator.querySelector(".status-dot");

    statusText.textContent = text;
    statusDot.className = `status-dot ${status}`;
  }

  showSystemStatus(data, isOnline) {
    const systemStatus = document.getElementById("systemStatus");

    if (isOnline) {
      systemStatus.innerHTML = `
                <div class="status-card success">
                    <i class="fas fa-check-circle"></i>
                    <div class="status-info">
                        <h3>Sistema Online</h3>
                        <p>Browser: ✅ | Scraping: ✅ | API: ✅</p>
                        <small>Testado com: @${
                          data.test_user || "instagram"
                        }</small>
                    </div>
                </div>
            `;
    } else {
      systemStatus.innerHTML = `
                <div class="status-card error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div class="status-info">
                        <h3>Sistema com Problemas</h3>
                        <p>${data.message || "Erro desconhecido"}</p>
                        <small>Verifique as dependências e tente novamente</small>
                    </div>
                </div>
            `;
    }
  }

  async startTracking() {
    if (this.isTracking) return;

    const formData = this.getFormData();
    if (!formData.username) {
      this.showToast("Por favor, insira um nome de usuário", "error");
      return;
    }

    this.isTracking = true;
    this.showProgress();
    this.hideResults();

    try {
      // Simular progresso
      this.updateProgress(0, "Iniciando rastreamento...");
      this.updateStep("step1", "active");

      await this.delay(1000);
      this.updateProgress(20, "Verificando usuário...");
      this.updateStep("step1", "completed");
      this.updateStep("step2", "active");

      // Fazer requisição para API
      const params = new URLSearchParams(formData);
      const response = await fetch(`${this.apiBase}/track?${params}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      this.updateProgress(40, "Processando dados...");
      this.updateStep("step2", "completed");
      this.updateStep("step3", "active");

      const data = await response.json();

      this.updateProgress(60, "Analisando atividades...");
      this.updateStep("step3", "completed");
      this.updateStep("step4", "active");

      await this.delay(1000);

      this.updateProgress(80, "Organizando resultados...");
      this.updateStep("step4", "completed");
      this.updateStep("step5", "active");

      await this.delay(500);

      this.updateProgress(100, "Concluído!");
      this.updateStep("step5", "completed");

      if (data.success) {
        this.currentResults = data;
        this.showResults(data);
        this.showToast(
          `Rastreamento concluído! ${data.total_activities} atividades encontradas`,
          "success"
        );
      } else {
        throw new Error(data.error || "Erro no rastreamento");
      }
    } catch (error) {
      console.error("Erro no rastreamento:", error);
      this.showToast(`Erro: ${error.message}`, "error");
      this.updateProgress(0, "Erro no rastreamento");
      this.resetSteps();
    } finally {
      this.isTracking = false;
      this.hideProgress();
    }
  }

  getFormData() {
    return {
      username: document
        .getElementById("targetUsername")
        .value.trim()
        .replace("@", ""),
      login_username: document.getElementById("loginUsername").value.trim(),
      login_password: document.getElementById("loginPassword").value.trim(),
      max_following: parseInt(document.getElementById("maxFollowing").value),
      headless:
        document.querySelector('input[name="headless"]:checked').value ===
        "true",
      ignore_pinned:
        document.querySelector('input[name="ignorePinned"]:checked').value ===
        "true",
      media_type: document.querySelector('input[name="mediaType"]:checked')
        .value,
      start_date: document.getElementById("startDate").value,
      end_date: document.getElementById("endDate").value,
      ignored_users: document.getElementById("ignoredUsers").value,
    };
  }

  showProgress() {
    document.getElementById("progressSection").style.display = "block";
    document.getElementById("trackBtn").style.display = "none";
    document.getElementById("stopBtn").style.display = "inline-flex";
    document.getElementById("loadingOverlay").style.display = "flex";
  }

  hideProgress() {
    document.getElementById("progressSection").style.display = "none";
    document.getElementById("trackBtn").style.display = "inline-flex";
    document.getElementById("stopBtn").style.display = "none";
    document.getElementById("loadingOverlay").style.display = "none";
  }

  updateProgress(percentage, text) {
    document.getElementById("progressFill").style.width = `${percentage}%`;
    document.getElementById("progressText").textContent = text;
    document.getElementById("loadingFill").style.width = `${percentage}%`;
    document.getElementById("loadingPercentage").textContent = `${percentage}%`;
    document.getElementById("loadingDescription").textContent = text;
  }

  updateStep(stepId, status) {
    const step = document.getElementById(stepId);
    step.className = `step ${status}`;

    const statusEl = step.querySelector(".step-status");
    if (status === "active") {
      statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    } else if (status === "completed") {
      statusEl.innerHTML = '<i class="fas fa-check"></i>';
    } else {
      statusEl.innerHTML = "";
    }
  }

  resetSteps() {
    document.querySelectorAll(".step").forEach((step) => {
      step.className = "step";
      step.querySelector(".step-status").innerHTML = "";
    });
  }

  showResults(data) {
    document.getElementById("resultsSection").style.display = "block";

    // Update stats
    this.updateStats(data);

    // Update metadata
    this.updateMetadata(data);

    // Update tab counts
    this.updateTabCounts(data);

    // Populate activities
    this.populateActivities(data.activities || []);

    // Scroll to results
    document
      .getElementById("resultsSection")
      .scrollIntoView({ behavior: "smooth" });
  }

  hideResults() {
    document.getElementById("resultsSection").style.display = "none";
  }

  updateStats(data) {
    const statsEl = document.getElementById("resultsStats");
    const activities = data.activity_types || {};

    statsEl.innerHTML = `
            <div class="stat-card">
                <div class="stat-number">${data.total_activities || 0}</div>
                <div class="stat-label">Total de Atividades</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${activities.outgoing_likes || 0}</div>
                <div class="stat-label">Curtidas Dadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${
                  activities.outgoing_comments || 0
                }</div>
                <div class="stat-label">Comentários Feitos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${activities.mentions || 0}</div>
                <div class="stat-label">Menções</div>
            </div>
        `;
  }

  updateMetadata(data) {
    const metadataEl = document.getElementById("metadataSection");
    const metadata = data.metadata || {};

    metadataEl.innerHTML = `
            <div class="metadata-card">
                <h4><i class="fas fa-info-circle"></i> Informações do Rastreamento</h4>
                <div class="metadata-grid">
                    <div class="metadata-item">
                        <span class="metadata-label">Usuário Rastreado:</span>
                        <span class="metadata-value">@${data.username}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Login Usado:</span>
                        <span class="metadata-value">${
                          metadata.login_used ? "✅ Sim" : "❌ Não"
                        }</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Browser Usado:</span>
                        <span class="metadata-value">${
                          metadata.browser_used ? "✅ Sim" : "❌ Não"
                        }</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Perfis Analisados:</span>
                        <span class="metadata-value">${
                          metadata.max_following_analyzed || 0
                        }</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Timestamp:</span>
                        <span class="metadata-value">${this.formatDate(
                          metadata.timestamp
                        )}</span>
                    </div>
                </div>
            </div>
        `;
  }

  updateTabCounts(data) {
    const activities = data.activity_types || {};

    document.getElementById("activitiesCount").textContent =
      data.total_activities || 0;
    document.getElementById("likesCount").textContent =
      activities.outgoing_likes || 0;
    document.getElementById("commentsCount").textContent =
      activities.outgoing_comments || 0;
  }

  populateActivities(activities) {
    // All activities
    this.populateActivityList("activitiesList", activities);

    // Likes only
    const likes = activities.filter((a) => a.type === "outgoing_like");
    this.populateActivityList("likesList", likes);

    // Comments only
    const comments = activities.filter((a) => a.type === "outgoing_comment");
    this.populateActivityList("commentsList", comments);

    // Summary
    this.populateSummary(activities);
  }

  populateActivityList(containerId, activities) {
    const container = document.getElementById(containerId);

    if (activities.length === 0) {
      container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>Nenhuma atividade encontrada</h3>
                    <p>Não foram encontradas atividades deste tipo para o usuário rastreado.</p>
                </div>
            `;
      return;
    }

    container.innerHTML = activities
      .map((activity) => this.createActivityCard(activity))
      .join("");
  }

  createActivityCard(activity) {
    const isComment = activity.type === "outgoing_comment";
    const isLike = activity.type === "outgoing_like";
    const isMention = activity.type === "mention";

    let icon, typeLabel, typeClass;

    if (isComment) {
      icon = "fas fa-comment";
      typeLabel = "Comentário";
      typeClass = "comment";
    } else if (isLike) {
      icon = "fas fa-heart";
      typeLabel = "Curtida";
      typeClass = "like";
    } else if (isMention) {
      icon = "fas fa-at";
      typeLabel = "Menção";
      typeClass = "mention";
    } else {
      icon = "fas fa-activity";
      typeLabel = "Atividade";
      typeClass = "activity";
    }

    return `
            <div class="activity-card ${typeClass}">
                <div class="activity-header">
                    <div class="activity-type">
                        <i class="${icon}"></i>
                        <span>${typeLabel}</span>
                    </div>
                    <div class="activity-date">
                        <i class="fas fa-clock"></i>
                        ${this.formatDate(activity.timestamp)}
                    </div>
                </div>
                
                <div class="activity-content">
                    ${
                      activity.target_user
                        ? `
                        <div class="activity-target">
                            <i class="fas fa-user"></i>
                            <strong>Para:</strong> @${activity.target_user}
                        </div>
                    `
                        : ""
                    }
                    
                    ${
                      activity.comment_text
                        ? `
                        <div class="activity-text">
                            <i class="fas fa-quote-left"></i>
                            <span>"${activity.comment_text}"</span>
                        </div>
                    `
                        : ""
                    }
                    
                    ${
                      activity.post_caption
                        ? `
                        <div class="activity-post-info">
                            <i class="fas fa-image"></i>
                            <span>Post: ${activity.post_caption.substring(
                              0,
                              100
                            )}${
                            activity.post_caption.length > 100 ? "..." : ""
                          }</span>
                        </div>
                    `
                        : ""
                    }
                    
                    ${
                      activity.media_type
                        ? `
                        <div class="activity-media-type">
                            <i class="fas fa-${
                              activity.media_type === "video"
                                ? "video"
                                : "image"
                            }"></i>
                            <span>Tipo: ${activity.media_type}</span>
                        </div>
                    `
                        : ""
                    }
                </div>
                
                ${
                  activity.post_url
                    ? `
                    <div class="activity-actions">
                        <a href="${activity.post_url}" target="_blank" class="btn btn-small">
                            <i class="fas fa-external-link-alt"></i>
                            Ver Post
                        </a>
                    </div>
                `
                    : ""
                }
            </div>
        `;
  }

  populateSummary(activities) {
    const summaryEl = document.getElementById("summaryContent");

    // Calculate statistics
    const stats = this.calculateStats(activities);

    summaryEl.innerHTML = `
            <div class="summary-grid">
                <div class="summary-card">
                    <h4><i class="fas fa-chart-bar"></i> Estatísticas Gerais</h4>
                    <div class="summary-stats">
                        <div class="summary-stat">
                            <span class="stat-label">Total de Atividades:</span>
                            <span class="stat-value">${activities.length}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Curtidas Dadas:</span>
                            <span class="stat-value">${stats.likes}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Comentários Feitos:</span>
                            <span class="stat-value">${stats.comments}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Usuários Únicos Interagidos:</span>
                            <span class="stat-value">${stats.uniqueUsers}</span>
                        </div>
                    </div>
                </div>
                
                <div class="summary-card">
                    <h4><i class="fas fa-users"></i> Usuários Mais Interagidos</h4>
                    <div class="top-users">
                        ${stats.topUsers
                          .map(
                            (user) => `
                            <div class="top-user">
                                <span class="user-name">@${user.username}</span>
                                <span class="user-count">${user.count} interações</span>
                            </div>
                        `
                          )
                          .join("")}
                    </div>
                </div>
                
                <div class="summary-card">
                    <h4><i class="fas fa-clock"></i> Atividade por Período</h4>
                    <div class="time-stats">
                        <p>Análise temporal das atividades encontradas</p>
                        <div class="summary-stat">
                            <span class="stat-label">Primeira Atividade:</span>
                            <span class="stat-value">${this.formatDate(
                              stats.firstActivity
                            )}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="stat-label">Última Atividade:</span>
                            <span class="stat-value">${this.formatDate(
                              stats.lastActivity
                            )}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  calculateStats(activities) {
    const likes = activities.filter((a) => a.type === "outgoing_like").length;
    const comments = activities.filter(
      (a) => a.type === "outgoing_comment"
    ).length;

    // Count unique users
    const userCounts = {};
    activities.forEach((activity) => {
      if (activity.target_user) {
        userCounts[activity.target_user] =
          (userCounts[activity.target_user] || 0) + 1;
      }
    });

    const uniqueUsers = Object.keys(userCounts).length;
    const topUsers = Object.entries(userCounts)
      .map(([username, count]) => ({ username, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // Time analysis
    const timestamps = activities
      .map((a) => new Date(a.timestamp))
      .filter((d) => !isNaN(d));
    const firstActivity =
      timestamps.length > 0 ? Math.min(...timestamps) : null;
    const lastActivity = timestamps.length > 0 ? Math.max(...timestamps) : null;

    return {
      likes,
      comments,
      uniqueUsers,
      topUsers,
      firstActivity,
      lastActivity,
    };
  }

  setupTabs() {
    // Tab functionality is handled by bindEvents
  }

  switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.remove("active");
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add("active");

    // Update tab content
    document.querySelectorAll(".tab-pane").forEach((pane) => {
      pane.classList.remove("active");
    });
    document.getElementById(tabName).classList.add("active");
  }

  async stopTracking() {
    try {
      await fetch(`${this.apiBase}/stop`, { method: "POST" });
      this.isTracking = false;
      this.hideProgress();
      this.showToast("Rastreamento interrompido", "info");
    } catch (error) {
      console.error("Erro ao parar rastreamento:", error);
    }
  }

  clearForm() {
    document.getElementById("trackingForm").reset();
    this.hideResults();
    this.hideProgress();
    this.currentResults = null;
  }

  formatDate(timestamp) {
    if (!timestamp) return "N/A";

    try {
      const date = new Date(timestamp);
      if (isNaN(date)) return "Data inválida";

      return date.toLocaleString("pt-BR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (error) {
      return "Data inválida";
    }
  }

  showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon;
    switch (type) {
      case "success":
        icon = "fas fa-check-circle";
        break;
      case "error":
        icon = "fas fa-exclamation-circle";
        break;
      case "warning":
        icon = "fas fa-exclamation-triangle";
        break;
      default:
        icon = "fas fa-info-circle";
    }

    toast.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (toast.parentElement) {
        toast.remove();
      }
    }, 5000);
  }

  delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new InstagramTracker();
});

// Export for testing
if (typeof module !== "undefined" && module.exports) {
  module.exports = InstagramTracker;
}
