document.addEventListener('DOMContentLoaded', function() {
    const formularioReserva = document.getElementById('formulario-reserva');
    const listaReservas = document.getElementById('lista-reservas');

    // Função para buscar reservas existentes
    function buscarReservas() {
        fetch('/api/listar-reservas')
            .then(response => response.json())
            .then(data => {
                if (listaReservas) {
                    listaReservas.innerHTML = '';
                    data.reservas.forEach(reserva => {
                        const itemLista = document.createElement('li');
                        itemLista.textContent = `${reserva.data_reserva} - ${reserva.horario_inicio}-${reserva.horario_fim} - ${reserva.nome}`;
                        listaReservas.appendChild(itemLista);
                    });
                }
            })
            .catch(error => console.error('Erro ao buscar reservas:', error));
    }

    // Event listener para submissão do formulário
    if (formularioReserva) {
        formularioReserva.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(formularioReserva);
            const dados = {
                nome: formData.get('nome'),

                data_reserva: formData.get('data_reserva'),
                horario_inicio: formData.get('horario_inicio'),
                horario_fim: formData.get('horario_fim'),
                email: formData.get('email'),
                telefone: formData.get('telefone'),
                numero_convidados: formData.get('numero_convidados'),
                observacoes: formData.get('observacoes')
            };

            fetch('/api/criar-reserva', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dados)
            })
            .then(response => response.json())
            .then(data => {
                if (data.sucesso) {
                    buscarReservas();
                    formularioReserva.reset();
                    alert('Reserva criada com sucesso!');
                } else {
                    alert('Erro: ' + data.mensagem);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro interno. Tente novamente.');
            });
        });
    }

    // Busca inicial de reservas
    if (listaReservas) {
        buscarReservas();
    }
});