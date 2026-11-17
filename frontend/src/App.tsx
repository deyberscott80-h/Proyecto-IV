import Swal from 'sweetalert2';
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';

import type { FormEvent } from 'react';

import { api } from './api';

import type {
  NewReview,
  Review,
  ReviewStats,
} from './types';

const initialForm: NewReview = {
  user_name: '',
  rating: 5,
  comment: '',
};

const initialStats: ReviewStats = {
  total_comments: 0,
  visible_comments: 0,
  hidden_comments: 0,
  answered_comments: 0,
  average_rating: 0,
};

const dateFormatter = new Intl.DateTimeFormat('es-CR', {
  dateStyle: 'long',
  timeZone: 'America/Costa_Rica',
});

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return dateFormatter.format(date);
}

function Stars({ rating }: { rating: number }) {
  return (
    <span
      className="stars"
      role="img"
      aria-label={`${rating} de 5 estrellas`}
    >
      {[1, 2, 3, 4, 5].map((number) => (
        <span
          key={number}
          className={
            number <= Math.round(rating)
              ? 'lit'
              : ''
          }
        >
          ★
        </span>
      ))}
    </span>
  );
}


async function confirmAction(
  title: string,
  message: string,
  confirmText: string,
  icon: 'question' | 'warning' = 'question'
): Promise<boolean> {
  const result = await Swal.fire({
    title,
    text: message,
    icon,
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: 'Cancelar',
    confirmButtonColor: '#6d4242',
    cancelButtonColor: '#88817d',
    reverseButtons: true,
    showClass: {
      popup: 'review-popup-show',
    },
    hideClass: {
      popup: 'review-popup-hide',
    },
  });

  return result.isConfirmed;
}


export function App() {

  const [reviews, setReviews] = useState<Review[]>([]);

  const [stats, setStats] = useState(initialStats);

  const [loading, setLoading] = useState(true);

  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState<NewReview>(initialForm);

  const [search, setSearch] = useState('');

  const [ratingFilter, setRatingFilter] = useState('all');

  const [visibilityFilter, setVisibilityFilter] =
    useState('all');

  const [showForm, setShowForm] = useState(false);

  const [editingReply, setEditingReply] =
    useState<number | null>(null);

  const [replyText, setReplyText] = useState('');

  const [error, setError] = useState('');

  const [notice, setNotice] = useState('');

  // ==========================================
  // RESEÑAS Y ESTADÍSTICAS
  // ==========================================

  const refresh = useCallback(async () => {
    const [reviewsData, statsData] = await Promise.all([
      api.list(),
      api.stats(),
    ]);

    setReviews(reviewsData);
    setStats(statsData);
  }, []);

  useEffect(() => {
    refresh()
      .catch((error) => {
        setError(
          error instanceof Error
            ? error.message
            : 'Error de conexión'
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, [refresh]);


  async function execute(
    action: () => Promise<unknown>,
    success: string
  ) {
    setSaving(true);
    setError('');
    setNotice('');

    try {
      await action();
      await refresh();

      setNotice(success);
      return true;
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : 'No se pudo completar la operación'
      );

      return false;
    } finally {
      setSaving(false);
    }
  }

  // ==========================================
  // CREAR UNA RESEÑA
  // ==========================================


  async function submit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const confirmed = await confirmAction(
      '¿Deseas publicar esta reseña?',
      'La reseña se guardará en el sistema.',
      'Sí, publicar'
    );

    if (!confirmed) {
      return;
    }

    const created = await execute(
      () =>
        api.create({
          ...form,
          user_name: form.user_name.trim(),
          comment: form.comment.trim(),
        }),
      'Reseña publicada correctamente.'
    );

    if (created) {
      setForm(initialForm);
      setShowForm(false);
    }
  }


  // ==========================================
  // FILTRAR RESEÑAS
  // ==========================================

  const filtered = useMemo(() => {
    return reviews.filter((review) => {
      const term = search
        .toLocaleLowerCase('es')
        .trim();

      const matchesSearch =
        review.user_name
          .toLocaleLowerCase('es')
          .includes(term) ||
        review.comment
          .toLocaleLowerCase('es')
          .includes(term);

      const matchesRating =
        ratingFilter === 'all' ||
        review.rating === Number(ratingFilter);

      const matchesVisibility =
        visibilityFilter === 'all' ||
        (
          visibilityFilter === 'visible'
            ? review.visible
            : !review.visible
        );

      return (
        matchesSearch &&
        matchesRating &&
        matchesVisibility
      );
    });
  }, [
    reviews,
    search,
    ratingFilter,
    visibilityFilter,
  ]);


  return (
    <div className="shell">

      <aside className="sidebar">

        <div className="brand">
          <span className="brand-symbol">
            A
          </span>

          <div className="brand-name">
            Alma
            <br />
            Inquebrantable
          </div>
        </div>

        <p className="side-caption">
          PANEL DE DEMOSTRACIÓN- Defensa2
        </p>

        <nav aria-label="Administración">

          <button
            className="nav-active"
            onClick={() => {
              setShowForm(false);
              setNotice('');
            }}
          >
            ☆ <span>Reseñas</span>
          </button>

          <button
            onClick={() => {
              setShowForm(true);
              setNotice('');
            }}
          >
            ＋ <span>Nueva reseña</span>
          </button>

        </nav>

        <div className="side-bottom">
          <span className="status-dot" />
          {' '}
          <br />
        </div>

      </aside>


      <div className="workspace">

        <header className="topbar">
          <span>
            Administración
            <span className="separator"> / </span>
            Reseñas
          </span>
        </header>

        <main className="content">

          <div className="hero">

            <div>
              <span className="eyebrow">
                ESCUCHA A TUS CLIENTES
              </span>

              <h1>Reseñas del negocio</h1>

              <p>
                Consulta las opiniones, administra
                respuestas y registra nuevas
                experiencias.
              </p>
            </div>

            <button
              className="primary"
              data-testid="toggle-form"
              onClick={() => {
                setShowForm((value) => !value);
              }}
            >
              {showForm
                ? 'Cerrar formulario'
                : '+ Nueva reseña'}
            </button>

          </div>

          {error && (
            <div
              className="message error"
              role="alert"
            >
              {error}
            </div>
          )}

          {notice && (
            <div
              className="message success"
              role="status"
            >
              {notice}
            </div>
          )}

          <section
            className="stats"
            aria-label="Estadísticas de reseñas"
          >

            <div className="stat">
              <span>Comentarios registrados</span>

              <strong data-testid="total-comments">
                {stats.total_comments}
              </strong>

              <small>Total de reseñas</small>
            </div>

            <div className="stat">
              <span>Calificación promedio</span>

              <strong>
                {stats.total_comments
                  ? stats.average_rating.toFixed(1)
                  : '—'}

                {' '}
                <span className="mini-star">
                  ★
                </span>
              </strong>

              <small>De 5 estrellas</small>
            </div>

            <div className="stat">
              <span>Comentarios visibles</span>

              <strong>
                {stats.visible_comments}
              </strong>

              <small>Publicados</small>
            </div>

            <div className="stat">
              <span>Respuestas enviadas</span>

              <strong>
                {stats.answered_comments}
              </strong>

              <small>Por el negocio</small>
            </div>

          </section>

          {showForm && (
            <section
              className="panel form-panel"
              aria-label="Crear reseña"
              data-testid="review-form"
            >

              <div className="section-header">
                <div>
                  <span className="eyebrow">
                    REGISTRAR EXPERIENCIA
                  </span>

                  <h2>Escribir una reseña</h2>
                </div>
              </div>

              <form onSubmit={submit}>

                <div className="form-row">

                  {/* NOMBRE */}

                  <label>
                    Nombre del usuario

                    <input
                      data-testid="review-user"
                      required
                      minLength={2}
                      maxLength={100}
                      value={form.user_name}
                      placeholder="Nombre del cliente"
                      onChange={(event) => {
                        setForm((current) => ({
                          ...current,
                          user_name: event.target.value,
                        }));
                      }}
                    />
                  </label>

                  <label>
                    Calificación

                    <select
                      data-testid="review-rating"
                      value={form.rating}
                      onChange={(event) => {
                        setForm((current) => ({
                          ...current,
                          rating: Number(
                            event.target.value
                          ),
                        }));
                      }}
                    >
                      {[5, 4, 3, 2, 1].map(
                        (number) => (
                          <option
                            key={number}
                            value={number}
                          >
                            {'★'.repeat(number)}
                            {' — '}
                            {number} estrellas
                          </option>
                        )
                      )}
                    </select>
                  </label>

                </div>

                <label>
                  Comentario (opcional)

                  <textarea
                    data-testid="review-comment"
                    maxLength={1000}
                    value={form.comment}
                    rows={4}
                    placeholder={
                      '¿Qué opinas de la atención ' +
                      'y experiencia en la tienda?'
                    }
                    onChange={(event) => {
                      setForm((current) => ({
                        ...current,
                        comment: event.target.value,
                      }));
                    }}
                  />
                </label>

                <div className="form-footer">

                  <button
                    className="primary"
                    type="submit"
                    data-testid="submit-review"
                    disabled={
                      saving ||
                      form.user_name.trim().length < 2
                    }
                  >
                    {saving
                      ? 'Guardando…'
                      : 'Publicar reseña'}
                  </button>

                </div>

              </form>

            </section>
          )}

          <section className="panel listing">

            <div className="section-header">

              <div>
                <span className="eyebrow">
                  GESTIÓN DE COMENTARIOS
                </span>

                <h2>
                  Todos los comentarios
                  {' '}
                  <span className="count">
                    {reviews.length}
                  </span>
                </h2>
              </div>

              <span className="results-number">
                {filtered.length} resultados
              </span>

            </div>

            <div className="filters">

              <label>
                Buscar comentario

                <input
                  data-testid="search-review"
                  type="search"
                  placeholder={
                    'Nombre o palabras ' +
                    'del comentario'
                  }
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                  }}
                />
              </label>

              <label>
                Calificación

                <select
                  data-testid="filter-rating"
                  value={ratingFilter}
                  onChange={(event) => {
                    setRatingFilter(event.target.value);
                  }}
                >
                  <option value="all">
                    Todas
                  </option>

                  {[5, 4, 3, 2, 1].map(
                    (number) => (
                      <option
                        key={number}
                        value={number}
                      >
                        {number} estrellas
                      </option>
                    )
                  )}
                </select>
              </label>

              <label>
                Visibilidad

                <select
                  data-testid="filter-visibility"
                  value={visibilityFilter}
                  onChange={(event) => {
                    setVisibilityFilter(
                      event.target.value
                    );
                  }}
                >
                  <option value="all">
                    Todas
                  </option>

                  <option value="visible">
                    Visibles
                  </option>

                  <option value="hidden">
                    Ocultas
                  </option>
                </select>
              </label>

            </div>

            {loading ? (

              <p className="empty">
                Cargando comentarios…
              </p>

            ) : filtered.length === 0 ? (

              <p
                className="empty"
                data-testid="empty-reviews"
              >
                No hay comentarios que coincidan
                con tu búsqueda.
              </p>

            ) : (

              <div
                className="review-grid"
                data-testid="reviews-list"
              >

                {filtered.map((review) => (

                  <article
                    className="review"
                    key={review.id}
                    data-testid="review-card"
                  >

                    <div className="review-top">

                      <div className="avatar">
                        {review.user_name
                          .slice(0, 1)
                          .toUpperCase()}
                      </div>

                      <div>
                        <h3>
                          {review.user_name}
                        </h3>

                        <small>
                          Publicado el{' '}
                          {formatDate(
                            review.published_at
                          )}
                        </small>
                      </div>

                      <span
                        className={
                          'pill ' +
                          (
                            review.visible
                              ? 'published'
                              : 'hidden'
                          )
                        }
                      >
                        {review.visible
                          ? 'Visible'
                          : 'Oculta'}
                      </span>

                    </div>

                    <div className="review-rating">

                      <Stars rating={review.rating} />

                      <span>
                        {review.rating} de 5
                      </span>

                    </div>


                    <p className="review-comment">
                      {review.comment}
                    </p>

                    {review.response && (

                      <div className="reply">

                        <b>Respuesta del negocio</b>

                        <p>
                          {review.response}
                        </p>

                      </div>

                    )}

                    {/* ==================================
                        FORMULARIO DE RESPUESTA
                        ================================== */}

                    {editingReply === review.id ? (

                      <div className="reply-form">

                        <label>
                          Responder comentario

                          <textarea
                            rows={3}
                            minLength={3}
                            maxLength={1000}
                            value={replyText}
                            onChange={(event) => {
                              setReplyText(
                                event.target.value
                              );
                            }}
                          />
                        </label>

                        <div className="actions">

                          <button
                            disabled={
                              saving ||
                              replyText.trim().length < 3
                            }

                            onClick={async () => {
                              const confirmed = await confirmAction(
                                '¿Deseas responder este comentario?',
                                'La respuesta será guardada.',
                                'Sí, responder'
                              );

                              if (!confirmed) {
                                return;
                              }

                              const saved = await execute(
                                () =>
                                  api.reply(
                                    review.id,
                                    replyText.trim()
                                  ),
                                'Respuesta guardada.'
                              );

                              if (saved) {
                                setEditingReply(null);
                                setReplyText('');
                              }
                            }}
                          >
                            Guardar respuesta
                          </button>

                          <button
                            className="text-button"
                            onClick={() => {
                              setEditingReply(null);
                            }}
                          >
                            Cancelar
                          </button>

                        </div>

                      </div>

                    ) : (

                      <div className="actions">

                        <button
                          onClick={() => {
                            setEditingReply(review.id);

                            setReplyText(
                              review.response ?? ''
                            );
                          }}
                        >
                          {review.response
                            ? 'Editar respuesta'
                            : 'Responder'}
                        </button>

                        <button
                          className="text-button"
                          disabled={saving}
                          onClick={() => {
                            void execute(
                              () =>
                                api.visibility(
                                  review.id,
                                  !review.visible
                                ),
                              'Visibilidad actualizada.'
                            );
                          }}
                        >
                          {review.visible
                            ? 'Ocultar'
                            : 'Mostrar'}
                        </button>

                        <button
                          className="text-button danger"
                          disabled={saving}

                          onClick={async () => {
                            const confirmed = await confirmAction(
                              '¿Deseas eliminar esta reseña?',
                              'Esta acción no se puede deshacer.',
                              'Sí, eliminar',
                              'warning'
                            );

                            if (!confirmed) {
                              return;
                            }

                            await execute(
                              () => api.delete(review.id),
                              'Reseña eliminada.'
                            );
                          }}

                        >
                          Eliminar
                        </button>

                      </div>

                    )}

                  </article>

                ))}

              </div>

            )}

          </section>

        </main>

      </div>

    </div>
  );
}
