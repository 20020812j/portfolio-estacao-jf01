document.addEventListener(
    "DOMContentLoaded",
    function () {

        const sidebar =
            document.getElementById(
                "sidebar"
            );

        const sidebarToggle =
            document.getElementById(
                "sidebarToggle"
            );

        const mobileMenuButton =
            document.getElementById(
                "mobileMenuButton"
            );

        const sidebarOverlay =
            document.getElementById(
                "sidebarOverlay"
            );


        /* =================================
           MENU DESKTOP
        ================================= */

        if (
            sidebar &&
            sidebarToggle
        ) {

            const estadoSalvo =
                localStorage.getItem(
                    "fisiosystem_sidebar"
                );


            if (
                estadoSalvo ===
                "collapsed"
            ) {

                sidebar.classList.add(
                    "collapsed"
                );

                document.body.classList.add(
                    "sidebar-is-collapsed"
                );

            }


            sidebarToggle.addEventListener(
                "click",
                function () {

                    sidebar.classList.toggle(
                        "collapsed"
                    );


                    document.body.classList.toggle(
                        "sidebar-is-collapsed"
                    );


                    const fechado =
                        sidebar.classList.contains(
                            "collapsed"
                        );


                    sidebarToggle.setAttribute(
                        "aria-expanded",
                        fechado ? "false" : "true"
                    );


                    if (fechado) {

                        localStorage.setItem(
                            "fisiosystem_sidebar",
                            "collapsed"
                        );

                    } else {

                        localStorage.setItem(
                            "fisiosystem_sidebar",
                            "expanded"
                        );

                    }

                }
            );

        }


        /* =================================
           MENU MOBILE
        ================================= */

        if (
            sidebar &&
            mobileMenuButton
        ) {

            mobileMenuButton.addEventListener(
                "click",
                function () {

                    sidebar.classList.add(
                        "mobile-open"
                    );


                    mobileMenuButton.setAttribute(
                        "aria-expanded",
                        "true"
                    );


                    if (
                        sidebarOverlay
                    ) {

                        sidebarOverlay
                            .classList
                            .add(
                                "active"
                            );

                    }


                    /* leva o foco de teclado para dentro do
                       menu recém-aberto */

                    const primeiroLink =
                        sidebar.querySelector(
                            ".sidebar-link"
                        );

                    primeiroLink?.focus();

                }
            );

        }


        /* FECHAR CLICANDO NO FUNDO */

        if (
            sidebar &&
            sidebarOverlay
        ) {

            sidebarOverlay.addEventListener(
                "click",
                function () {

                    sidebar.classList.remove(
                        "mobile-open"
                    );


                    sidebarOverlay
                        .classList
                        .remove(
                            "active"
                        );


                    mobileMenuButton?.setAttribute(
                        "aria-expanded",
                        "false"
                    );

                }
            );

        }


        /* =================================
           FECHAR MENU MOBILE AO CLICAR
           EM UM LINK
        ================================= */

        const links =
            document.querySelectorAll(
                ".sidebar-link"
            );


        links.forEach(
            function (link) {

                link.addEventListener(
                    "click",
                    function () {

                        if (
                            window.innerWidth <=
                            980
                        ) {

                            sidebar
                                ?.classList
                                .remove(
                                    "mobile-open"
                                );


                            sidebarOverlay
                                ?.classList
                                .remove(
                                    "active"
                                );


                            mobileMenuButton?.setAttribute(
                                "aria-expanded",
                                "false"
                            );

                        }

                    }
                );

            }
        );


        /* =================================
           FECHAR MENU MOBILE COM A TECLA ESC
        ================================= */

        document.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Escape" &&
                    sidebar?.classList.contains(
                        "mobile-open"
                    )
                ) {

                    sidebar.classList.remove(
                        "mobile-open"
                    );


                    sidebarOverlay
                        ?.classList
                        .remove(
                            "active"
                        );


                    mobileMenuButton?.setAttribute(
                        "aria-expanded",
                        "false"
                    );


                    mobileMenuButton?.focus();

                }

            }
        );


        /* =================================
           TEXTAREA AUTOMÁTICO
        ================================= */

        document
            .querySelectorAll(
                "textarea"
            )
            .forEach(
                function (textarea) {

                    textarea.addEventListener(
                        "input",
                        function () {

                            textarea.style.height =
                                "auto";


                            textarea.style.height =
                                Math.min(
                                    textarea.scrollHeight,
                                    300
                                ) +
                                "px";

                        }
                    );

                }
            );


        /* =================================
           CORRIGE MENU AO REDIMENSIONAR
        ================================= */

        window.addEventListener(
            "resize",
            function () {

                if (
                    window.innerWidth >
                    980
                ) {

                    sidebar
                        ?.classList
                        .remove(
                            "mobile-open"
                        );


                    sidebarOverlay
                        ?.classList
                        .remove(
                            "active"
                        );


                    mobileMenuButton?.setAttribute(
                        "aria-expanded",
                        "false"
                    );

                }

            }
        );


        /* =================================
           EVITA DUPLO ENVIO DE FORMULÁRIOS
           (desabilita o botão ao salvar, mostrando
           que a ação está em andamento)
        ================================= */

        document
            .querySelectorAll("form")
            .forEach(function (form) {

                form.addEventListener(
                    "submit",
                    function (event) {

                        /* se outro handler (ex: confirm()
                           de uma ação destrutiva) já
                           cancelou o envio, não mexe no
                           botão */

                        if (event.defaultPrevented) {
                            return;
                        }

                        const botao =
                            form.querySelector(
                                'button[type="submit"], button:not([type])'
                            );

                        if (!botao || botao.disabled) {
                            return;
                        }

                        /* deixa o navegador validar o
                           formulário (campos required, etc.)
                           antes de travar o botão */

                        if (!form.checkValidity()) {
                            return;
                        }

                        const textoOriginal =
                            botao.textContent;

                        botao.disabled = true;
                        botao.setAttribute(
                            "aria-disabled",
                            "true"
                        );
                        botao.dataset.textoOriginal =
                            textoOriginal;
                        botao.textContent =
                            "Salvando...";

                    }
                );

            });


    }
);