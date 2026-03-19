import re
import subprocess

# get original dashboard html from main branch
process = subprocess.Popen(['git', 'show', 'origin/main:templates/dashboard.html'], stdout=subprocess.PIPE)
original_html, _ = process.communicate()
original_html = original_html.decode('utf-8')

main_content_match = re.search(r'<main class="main-content">(.*?)</main>', original_html, re.DOTALL)
main_content = main_content_match.group(1) if main_content_match else ""

dashboard_js_match = re.search(r'<script type="module">.*?</script>', original_html, re.DOTALL)
dashboard_js = dashboard_js_match.group(0) if dashboard_js_match else ""

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
            <div class="relative hidden md:block">
                <i data-lucide="search" class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
                <input type="text" placeholder="Buscar em tudo..." class="pl-10 pr-4 py-2 bg-gray-50 border-none rounded-full w-64 focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all text-sm outline-none">
            </div>

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

        <!-- NEW FORM FOR BACKEND COMPATIBILITY -->
        <div class="glass-card p-6 mb-8 animate-fade-in-up">
            <h3 class="font-bold text-xl text-gray-800 display-font mb-4">Nova Busca de Perfil</h3>
            <!-- O JS Dashboard.js intercepta form de tracking-form ou similar? Pelo que vi no dashboard origin ele usa id="search-form" na topbar -->
            <form id="search-form" class="flex flex-col md:flex-row gap-4">
              <input type="text" id="target-username" class="flex-1 p-3 border rounded-xl" placeholder="@username" required>
              <button type="submit" class="bg-teal-gradient text-white px-6 py-3 rounded-xl font-bold hover:shadow-lg transition">Iniciar Tracking</button>
            </form>
        </div>

        <!-- ORIGINAL HTML APP STRUCTURE WRAPPED IN A COSMIC CARD -->
        <div class="glass-card p-6 min-h-[600px] overflow-hidden">
             <!-- Injecting the original main-content so the JS can find its DOM elements -->
             <div class="main-content">
{main_content}
             </div>
        </div>
    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.1/socket.io.js"></script>
    <script>lucide.createIcons();</script>
    {dashboard_js}
</body>
</html>
"""

with open('templates/dashboard.html', 'w') as f:
    f.write(html)
