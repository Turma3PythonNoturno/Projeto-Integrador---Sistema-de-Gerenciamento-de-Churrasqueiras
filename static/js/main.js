
document.addEventListener('DOMContentLoaded', function() {
    const formReserva = document.getElementById('form-reserva');
    const dataReserva = document.getElementById('data_reserva');
    const horarioInicio = document.getElementById('horario_inicio');
    const horarioFim = document.getElementById('horario_fim');
    const selectChurrasqueira = document.getElementById('churrasqueira_id');
    const verificacaoDiv = document.getElementById('verificacao-disponibilidade');
    const resultadoDiv = document.getElementById('resultado-disponibilidade');
    const mensagemDiv = document.getElementById('mensagem');
    const botaoSubmit = document.getElementById('botao-submit');

    // Elementos associados
    const cpfInput = document.getElementById('cpf_associado');
    const nomeInput = document.getElementById('nome');
    const emailInput = document.getElementById('email');
    const telefoneInput = document.getElementById('telefone');
    const statusAssociadoDiv = document.getElementById('status-associado');

    // Datas mínima e máxima
    const hoje = new Date();
    const amanha = new Date(hoje);
    amanha.setDate(amanha.getDate() + 1);
    dataReserva.min = amanha.toISOString().split('T')[0];

    const dataMaxima = new Date(hoje);
    dataMaxima.setDate(dataMaxima.getDate() + 30);
    dataReserva.max = dataMaxima.toISOString().split('T')[0];

    // Gerar opções de horário
    function gerarOpcoesHorario(selectElement) {
        selectElement.innerHTML = '<option value="">Selecione...</option>';
        for (let h = 8; h <= 22; h++) {
            for (let m = 0; m < 60; m += 30) {
                const horario = String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
                const option = document.createElement('option');
                option.value = horario;
                option.textContent = horario;
                selectElement.appendChild(option);
            }
        }
    }
    gerarOpcoesHorario(horarioInicio);
    gerarOpcoesHorario(horarioFim);

    // CPF
    function formatarCPF(cpf) {
        cpf = cpf.replace(/\D/g, '');
        cpf = cpf.replace(/(\d{3})(\d)/, '$1.$2');
        cpf = cpf.replace(/(\d{3})(\d)/, '$1.$2');
        cpf = cpf.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        return cpf;
    }

    function validarCPF(cpf) {
        cpf = cpf.replace(/\D/g, '');
        if (cpf.length !== 11) return false;
        if (/^(\d)\1{10}$/.test(cpf)) return false;

        let soma = 0;
        for (let i = 0; i < 9; i++) soma += parseInt(cpf[i]) * (10 - i);
        let resto = soma % 11;
        let dig1 = resto < 2 ? 0 : 11 - resto;
        if (parseInt(cpf[9]) !== dig1) return false;

        soma = 0;
        for (let i = 0; i < 10; i++) soma += parseInt(cpf[i]) * (11 - i);
        resto = soma % 11;
        let dig2 = resto < 2 ? 0 : 11 - resto;
        return parseInt(cpf[10]) === dig2;
    }

    function limparCamposAssociado() {
        nomeInput.value = '';
        emailInput.value = '';
        telefoneInput.value = '';
    }

    function buscarAssociado(cpf) {
        const cpfLimpo = cpf.replace(/\D/g, '');
        if (cpfLimpo.length !== 11 || !validarCPF(cpfLimpo)) {
            limparCamposAssociado();
            statusAssociadoDiv.innerHTML = '<div style="color: red; font-weight: bold;">❌ CPF inválido</div>';
            return;
        }

        statusAssociadoDiv.innerHTML = '<div style="color: #666;">🔄 Buscando associado...</div>';

        fetch(`/api/associado/verificar/${cpfLimpo}`)
            .then(r => r.json())
            .then(data => {
                if (!data.encontrado) {
                    limparCamposAssociado();
                    statusAssociadoDiv.innerHTML = `<div style="color: red; font-weight: bold;">❌ ${data.mensagem}</div>`;
                } else {
                    nomeInput.value = data.associado.nome || '';
                    emailInput.value = data.associado.email || '';
                    telefoneInput.value = data.associado.telefone || '';
                    if (data.adimplente) {
                        statusAssociadoDiv.innerHTML = '<div style="color: green; font-weight: bold;">✅ Associado encontrado e adimplente</div>';
                    } else {
                        statusAssociadoDiv.innerHTML = '<div style="color: red; font-weight: bold;">❌ Associado encontrado, mas NÃO adimplente. Não pode fazer reservas.</div>';
                    }
                }
                atualizarBotao();
            })
            .catch(err => {
                console.error(err);
                limparCamposAssociado();
                statusAssociadoDiv.innerHTML = '<div style="color: red; font-weight: bold;">❌ Erro ao buscar associado.</div>';
                atualizarBotao();
            });
    }

    cpfInput.addEventListener('input', e => {
        e.target.value = formatarCPF(e.target.value);
        const cpfLimpo = e.target.value.replace(/\D/g, '');
        if (cpfLimpo.length === 11) buscarAssociado(e.target.value);
        else {
            limparCamposAssociado();
            statusAssociadoDiv.innerHTML = '';
            atualizarBotao();
        }
    });

    // Verificação de disponibilidade
    // ------------------------------
// ATUALIZAR CHURRASQUEIRAS
// ------------------------------
    function atualizarChurrasqueiras() {
        const data = document.getElementById("data_reserva").value; 
        const inicio = document.getElementById("horario_inicio").value;
        const fim = document.getElementById("horario_fim").value;
        const select = document.getElementById("churrasqueira_id");
        const botao = document.getElementById("botao-submit");

        // Desabilita o botão e reseta o select
        botao.disabled = true;
        select.innerHTML = '<option value="">Carregando...</option>';

        // Só faz busca quando tudo estiver preenchido
        if (!data || !inicio || !fim) {
            select.innerHTML = '<option value="">Selecione a data e horários primeiro...</option>';
            return;
        }

        fetch(`/reservas/disponiveis?data=${data}&inicio=${inicio}&fim=${fim}`)
            .then(r => r.json())
            .then(json => {
                select.innerHTML = '<option value="">Selecione...</option>';

                if (!json.disponiveis || json.disponiveis.length === 0) {
                    select.innerHTML = '<option value="">Nenhuma disponível</option>';
                    return;
                }

                json.disponiveis.forEach(ch => {
                    const op = document.createElement("option");
                    op.value = ch.id;
                    op.textContent = ch.nome;
                    select.appendChild(op);
                });
            })
            .catch(err => {
                console.error("Erro ao buscar churrasqueiras:", err);
                select.innerHTML = '<option value="">Erro ao carregar</option>';
            });
    }

    // ------------------------------
    // QUANDO MUDAR DATA / INÍCIO / FIM
    // ------------------------------
    document.getElementById("data_reserva").addEventListener("change", () => {
        atualizarChurrasqueiras();
        verificarDisponibilidade();
    });

    document.getElementById("horario_inicio").addEventListener("change", () => {
        atualizarChurrasqueiras();
        verificarDisponibilidade();
    });

    document.getElementById("horario_fim").addEventListener("change", () => {
        atualizarChurrasqueiras();
        verificarDisponibilidade();
    });

    // ------------------------------
    // DEBUG E HABILITAÇÃO DO BOTÃO
    // ------------------------------
    document.getElementById("churrasqueira_id").addEventListener("change", function () {
        const valor = this.value;
        const debug = document.getElementById("debug-id");
        const botao = document.getElementById("botao-submit");

        if (valor) {
            debug.textContent = "ID selecionado: " + valor;
            botao.disabled = false;
        } else {
            debug.textContent = "Nenhuma churrasqueira selecionada";
            botao.disabled = true;
        }
    });

    // ------------------------------
    // FORÇAR QUE O SUBMIT SÓ ENVIE SE A CHURRASQUEIRA EXISTIR
    // ------------------------------
    formReserva.addEventListener("submit", function (e) {
        e.preventDefault();

        const id = document.getElementById("churrasqueira_id").value;

        if (!id) {
            alert("Selecione uma churrasqueira antes de continuar!");
            return;
        }

        const formData = new FormData(formReserva);
        const dados = {};

        for (let [key, value] of formData.entries()) {
            dados[key] = value;
        }

        fetch("/api/criar-reserva", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        })
        .then(r => r.json())
        .then(data => {
            if (data.sucesso) {
                mensagemDiv.className = "alert alert-success";
                mensagemDiv.innerHTML = `${data.mensagem}<br><small>ID: ${data.reserva_id}</small>`;
                mensagemDiv.style.display = "block";

                setTimeout(() => {
                    window.location.href = "/reservas";
                }, 2000);
            } else {
                mensagemDiv.className = "alert alert-error";
                mensagemDiv.innerHTML = data.mensagem;
                mensagemDiv.style.display = "block";
            }
        })
        .catch(err => {
            mensagemDiv.className = "alert alert-error";
            mensagemDiv.innerHTML = "Erro interno ao salvar.";
            mensagemDiv.style.display = "block";
            console.error(err);
        });

    // ------------------------------
    // CANCELAMENTO DE RESERVAS
    // ------------------------------
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('button[data-action="cancelar"]');
        if (!btn) return;

        const reservaId = btn.getAttribute('data-id');
        if (!reservaId) return;

        // Confirmação pelo usuário
        if (!confirm('tem certeza que deseja cancelar a reserva')) return;

        // Desabilitar botão enquanto processa
        btn.disabled = true;

        fetch(`/api/cancelar-reserva/${reservaId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        })
        .then(r => r.json())
        .then(data => {
            if (data.sucesso) {
                // Atualizar badge de status
                const statusEl = document.getElementById(`status-${reservaId}`);
                if (statusEl) {
                    statusEl.textContent = 'Cancelada';
                    statusEl.style.backgroundColor = '#6c757d';
                }

                // Atualizar botão
                btn.textContent = 'Cancelado';
                btn.style.opacity = '0.6';
                btn.disabled = true;

                alert(data.mensagem || 'Reserva cancelada com sucesso');
            } else {
                alert(data.mensagem || 'Não foi possível cancelar a reserva');
                btn.disabled = false;
            }
        })
        .catch(err => {
            console.error(err);
            alert('Erro ao cancelar reserva');
            btn.disabled = false;
        });
    });
    });
