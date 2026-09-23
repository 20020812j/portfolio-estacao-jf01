const setores = document.querySelectorAll(".setor");
const modal = document.getElementById("modal");
const conteudoModal = document.getElementById("conteudo-modal");
const fechar = document.getElementById("fechar");

const codigoModal = document.getElementById("codigo-modal");
const fecharCodigo = document.getElementById("fechar-codigo");
const listaArquivos = document.getElementById("lista-arquivos");
const codigoExibido = document.getElementById("codigo-exibido");
const nomeArquivo = document.getElementById("nome-arquivo");
const copiarCodigo = document.getElementById("copiar-codigo");
const codigoTitulo = document.getElementById("codigo-titulo");

const conteudos = {
    sobre: `
        <h2 class="titulo-setor">SOBRE MIM</h2>
        <p class="texto-setor">
            Sou José Flaviano, estudante de Desenvolvimento de Sistemas,
            com foco em desenvolvimento web e construção de aplicações práticas.
        </p>
    `,
    tecnologias: `
        <h2 class="titulo-setor">TECNOLOGIAS</h2>
        <div class="lista-tecnologias">
            <span>HTML5</span><span>CSS3</span><span>JavaScript</span>
            <span>Python</span><span>Flask</span><span>SQL</span>
            <span>PostgreSQL</span><span>Git</span><span>GitHub</span>
        </div>
    `,
    experiencia: `
        <h2 class="titulo-setor">EXPERIÊNCIA</h2>
        <p class="texto-setor">
            Experiência profissional em ambiente de produção e desenvolvimento
            de projetos próprios e para negócios reais.
        </p>
    `,
    formacao: `
        <h2 class="titulo-setor">FORMAÇÃO</h2>
        <p class="texto-setor">
            Técnico em Desenvolvimento de Sistemas — Proz Educação.
        </p>
    `,
    jornada: `
        <h2 class="titulo-setor">JORNADA</h2>
        <p class="texto-setor">
            Da aprendizagem dos fundamentos até aplicações web completas,
            com banco de dados, autenticação, APIs e publicação na internet.
        </p>
    `,
    projetos: `
        <h2 class="titulo-setor">PROJETOS</h2>

        <div class="projeto">
            <h3>FisioSystem</h3>
            <p>Sistema web para gerenciamento de clínica de fisioterapia.</p>
            <div class="lista-tecnologias">
                <span>Python</span><span>Flask</span><span>PostgreSQL</span>
                <span>HTML</span><span>CSS</span><span>JavaScript</span>
            </div>
            <a class="botao-projeto" href="https://fisiosytem.onrender.com" target="_blank">🌐 Abrir projeto</a>
            <button class="botao-projeto explorar-codigo" data-projeto="FISIOSYSTEM">💻 Explorar código</button>
        </div>

        <div class="projeto">
            <h3>Claudia Delícias Caseiras</h3>
            <p>Site de pedidos desenvolvido para um negócio real de alimentação.</p>
            <div class="lista-tecnologias">
                <span>Python</span><span>Flask</span><span>SQLite</span>
                <span>HTML</span><span>CSS</span><span>JavaScript</span>
            </div>
            <a class="botao-projeto" href="https://claudia-delicias-caseiras.onrender.com" target="_blank">🌐 Abrir projeto</a>
            <button class="botao-projeto explorar-codigo" data-projeto="CLAUDIA">💻 Explorar código</button>
        </div>
    `
};

setores.forEach(setor => {
    setor.addEventListener("click", () => {
        conteudoModal.innerHTML = conteudos[setor.dataset.setor];
        modal.classList.add("ativo");
        ativarExploradores();
    });
});

fechar.addEventListener("click", () => modal.classList.remove("ativo"));

modal.addEventListener("click", e => {
    if (e.target === modal) modal.classList.remove("ativo");
});

function ativarExploradores() {
    document.querySelectorAll(".explorar-codigo").forEach(botao => {
        botao.addEventListener("click", () => abrirCodigo(botao.dataset.projeto));
    });
}

async function abrirCodigo(projeto) {
    codigoTitulo.textContent = projeto === "FISIOSYSTEM"
        ? "FISIOSYSTEM — EXPLORADOR DE CÓDIGO"
        : "CLAUDIA DELÍCIAS — EXPLORADOR DE CÓDIGO";

    listaArquivos.innerHTML = "";
    codigoExibido.textContent = "";
    nomeArquivo.textContent = "Selecione um arquivo";
    codigoModal.classList.add("ativo");

    try {
        const resposta = await fetch("codigo-manifest.json");
        const manifest = await resposta.json();

        manifest[projeto].forEach((arquivo, index) => {
            const botao = document.createElement("button");
            botao.className = "arquivo-btn";
            botao.textContent = arquivo;
            botao.addEventListener("click", () => carregarArquivo(projeto, arquivo, botao));
            listaArquivos.appendChild(botao);

            if (index === 0) carregarArquivo(projeto, arquivo, botao);
        });
    } catch (erro) {
        codigoExibido.textContent =
            "Não foi possível carregar a lista de arquivos.\n\n" +
            "Se você estiver abrindo o index.html diretamente pelo computador, " +
            "publique o portfólio em um servidor local ou hospedagem.";
    }
}

async function carregarArquivo(projeto, arquivo, botao) {
    document.querySelectorAll(".arquivo-btn").forEach(b => b.classList.remove("ativo"));
    botao.classList.add("ativo");

    nomeArquivo.textContent = arquivo;

    try {
        const resposta = await fetch(`codigo/${projeto.toLowerCase()}/${arquivo}`);
        if (!resposta.ok) throw new Error("Arquivo não encontrado");

        const texto = await resposta.text();
        codigoExibido.textContent = texto;
        copiarCodigo.dataset.codigo = texto;
    } catch (erro) {
        codigoExibido.textContent = "Não foi possível carregar este arquivo.";
    }
}

copiarCodigo.addEventListener("click", async () => {
    const texto = copiarCodigo.dataset.codigo || codigoExibido.textContent;

    try {
        await navigator.clipboard.writeText(texto);
        copiarCodigo.textContent = "✓ Copiado!";
        setTimeout(() => copiarCodigo.textContent = "📋 Copiar", 1500);
    } catch {
        copiarCodigo.textContent = "Erro ao copiar";
        setTimeout(() => copiarCodigo.textContent = "📋 Copiar", 1500);
    }
});

fecharCodigo.addEventListener("click", () => codigoModal.classList.remove("ativo"));

codigoModal.addEventListener("click", e => {
    if (e.target === codigoModal) codigoModal.classList.remove("ativo");
});
