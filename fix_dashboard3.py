import re
import subprocess

# Read original file completely to analyze and extract the proper selectors that JS might use
process = subprocess.Popen(['git', 'show', 'origin/main:templates/dashboard.html'], stdout=subprocess.PIPE)
original_html, _ = process.communicate()
original_html = original_html.decode('utf-8')

# Grab the whole <main class="main-content"> ... </main> block
main_content_match = re.search(r'<main class="main-content">(.*?)</main>', original_html, re.DOTALL)
main_content = main_content_match.group(1) if main_content_match else ""

# Grab the script block at the end
dashboard_js_match = re.search(r'<script type="module">.*?</script>', original_html, re.DOTALL)
dashboard_js = dashboard_js_match.group(0) if dashboard_js_match else ""

# Replace dashboard.html to merge new bento grid with original backend integrations
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Centro de Comando Estelar - Lyra Tracker</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"/>
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body class="bg-[#F8F7FC] min-h-screen text-gray-900 font-sans antialiased overflow-x-hidden">

    <!-- Navbar / Header -->
    <header class="fixed top-0 left-0 right-0 h-16 bg-white/80 backdrop-blur-md border-b border-gray-100 z-40 flex items-center justify-between px-6 transition-all duration-300 md:ml-64">
        <div class="flex items-center gap-4">
            <button id="mobile-menu-btn" class="p-2 -ml-2 rounded-lg text-gray-500 hover:bg-gray-100 md:hidden transition-colors">
                <i data-lucide="menu" class="w-6 h-6"></i>
            </button>
            <h1 class="text-xl font-bold display-font hidden sm:block">Dashboard</h1>
        </div>

        <div class="flex items-center gap-4">
            <!-- Form search-form for Dashboard.js compatibility -->
            <form id="search-form" class="relative hidden md:flex items-center">
                <i data-lucide="search" class="w-5 h-5 absolute left-3 text-gray-400"></i>
                <input type="text" id="target-username" placeholder="Buscar perfil..." class="pl-10 pr-4 py-2 bg-gray-50 border-none rounded-full w-64 focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all text-sm outline-none">
            </form>

            <button class="relative p-2 rounded-full text-gray-500 hover:bg-teal-50 hover:text-teal-600 transition-colors">
                <i data-lucide="bell" class="w-6 h-6"></i>
                <span class="absolute top-1 right-1 w-2.5 h-2.5 bg-coral-500 rounded-full animate-pulse"></span>
            </button>

            <div class="h-8 w-px bg-gray-200 hidden sm:block"></div>

            <button class="flex items-center gap-2 group p-1 pr-3 rounded-full hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100">
                <img src="https://ui-avatars.com/api/?name=Admin+Lyra&background=e0f2f1&color=00897b" alt="Avatar" class="w-8 h-8 rounded-full shadow-sm">
                <span class="text-sm font-semibold hidden sm:block">Admin Lyra</span>
                <i data-lucide="chevron-down" class="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors"></i>
            </button>
        </div>
    </header>

    {{% include 'sidebar_fixed.html' %}}

    <!-- Main Content Bento Grid -->
    <main class="pt-24 pb-12 px-4 md:px-8 max-w-7xl mx-auto md:ml-64 transition-all duration-300">
        
        <div class="mb-8 animate-fade-in-up">
            <h2 class="text-3xl font-bold display-font mb-2">Bem-vindo(a) de volta, Admin! ✨</h2>
            <p class="text-gray-500 text-lg">Aqui está o panorama da sua jornada de longevidade cósmica hoje.</p>
        </div>

        <!-- Bento Grid with Cosmic Visuals and integrated legacy classes -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in" style="animation-delay: 0.1s;">
            
            <!-- Vitais Resumo / User Profile (Span 2) -->
            <div class="glass-card md:col-span-2 p-6 flex flex-col justify-between relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
                    <i data-lucide="heart-pulse" class="w-32 h-32 text-teal-600"></i>
                </div>
                <div>
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2.5 bg-teal-100 text-teal-600 rounded-xl">
                            <i data-lucide="activity" class="w-6 h-6"></i>
                        </div>
                        <h3 class="font-bold text-xl text-gray-800 display-font">Perfil Rastreado</h3>
                    </div>
                    <!-- Legacy integration point: where Dashboard.js injects user info -->
                    <div id="profile-container" class="profile-header">
                        <p class="text-gray-500 mb-6 text-sm">Pesquise um usuário na barra de busca para carregar as métricas do perfil.</p>
                    </div>
                </div>

                <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
                    <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                        <div class="text-gray-400 mb-1 flex items-center justify-between">
                            <span class="text-xs font-semibold uppercase tracking-wide">BPM Médio</span>
                            <i data-lucide="heart" class="w-4 h-4 text-rose-400"></i>
                        </div>
                        <div class="text-2xl font-bold text-gray-800" id="stat-bpm">-- <span class="text-sm font-normal text-gray-500">bpm</span></div>
                    </div>
                    <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                        <div class="text-gray-400 mb-1 flex items-center justify-between">
                            <span class="text-xs font-semibold uppercase tracking-wide">Qualidade do Sono</span>
                            <i data-lucide="moon" class="w-4 h-4 text-indigo-400"></i>
                        </div>
                        <div class="text-2xl font-bold text-gray-800" id="stat-sleep">-- <span class="text-sm font-normal text-gray-500">h</span></div>
                    </div>
                    <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                        <div class="text-gray-400 mb-1 flex items-center justify-between">
                            <span class="text-xs font-semibold uppercase tracking-wide">Atividade Física</span>
                            <i data-lucide="footprints" class="w-4 h-4 text-teal-400"></i>
                        </div>
                        <div class="text-2xl font-bold text-gray-800" id="stat-steps">--</div>
                    </div>
                    <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                        <div class="text-gray-400 mb-1 flex items-center justify-between">
                            <span class="text-xs font-semibold uppercase tracking-wide">Saúde Geral</span>
                            <i data-lucide="waves" class="w-4 h-4 text-blue-400"></i>
                        </div>
                        <div class="text-2xl font-bold text-gray-800" id="stat-health">-- <span class="text-sm font-normal text-gray-500">%</span></div>
                    </div>
                </div>
            </div>

            <!-- IA Assistente / Live Tracker Status -->
            <div class="glass-card p-6 border-l-4 border-l-purple-500 relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
                    <i data-lucide="brain" class="w-24 h-24 text-purple-600"></i>
                </div>
                <div class="flex items-center gap-3 mb-4">
                    <div class="p-2.5 bg-purple-100 text-purple-600 rounded-xl">
                        <i data-lucide="sparkles" class="w-6 h-6"></i>
                    </div>
                    <h3 class="font-bold text-xl text-gray-800 display-font">Tracker IA</h3>
                </div>
                
                <div id="status-container" class="status-indicator">
                    <span class="status-dot"></span> <span id="current-status">Pronto para iniciar</span>
                </div>
                
                <div id="live-events" class="live-events mt-4 mb-6 max-h-40 overflow-y-auto border border-gray-100 rounded-xl p-3 bg-white/50 text-sm space-y-2">
                    <!-- Events injected by Dashboard.js -->
                    <div class="text-gray-400 text-center italic">Aguardando eventos...</div>
                </div>

                <button id="btn-toggle-tracking" class="w-full py-2.5 px-4 rounded-xl bg-purple-50 text-purple-700 font-semibold text-sm hover:bg-purple-100 transition-colors flex items-center justify-center gap-2 group-hover:shadow-sm" disabled>
                    <i data-lucide="play-circle" class="w-4 h-4"></i>
                    Iniciar Tracking
                </button>
            </div>
            
            <!-- Analysis Section (Span 3) encapsulating the original tabs logic but hidden cleanly or presented in scrolling view -->
            <div class="glass-card md:col-span-3 p-6 mt-8">
               <div class="flex items-center gap-3 mb-6">
                    <div class="p-2.5 bg-coral-50 text-coral-500 rounded-xl">
                        <i data-lucide="target" class="w-6 h-6"></i>
                    </div>
                    <h3 class="font-bold text-xl text-gray-800 display-font">Módulos de Inteligência Avançada</h3>
                </div>
                
                <!-- ORIGINAL TABS & WIDGETS WRAPPED -->
                <div class="main-content" style="padding: 0; background: transparent;">
{main_content}
                </div>
            </div>

        </div>
    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.1/socket.io.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>lucide.createIcons();</script>
    {dashboard_js}
</body>
</html>
"""

with open('templates/dashboard.html', 'w') as f:
    f.write(html)
