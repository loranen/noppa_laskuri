import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Page setup ----------------
st.set_page_config(
    page_title="Pisteiden seuranta",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------- Language in session (default: Finnish) ----------------
if "lang" not in st.session_state:
    st.session_state.lang = "Suomi"

TXT_DICT = {
    "English": {
        "title": "Points Tracker",
        "add_players": "Add Players (2 or more)",
        "start_game": "Start Game",
        "name_prompt": "Enter player names separated by commas",
        "round": "Round",
        "turn": "'s turn",
        "points_for": "Points for",
        "end_turn": "End Turn",
        "undo": "Undo Last Turn",
        "scores": "Scores by Round",
        "next_up": "Next up",
        "press_enter": "Press Enter to end turn",
        "total": "Total",
        "need_two": "Please enter at least two players.",
    },
    "Suomi": {
        "title": "Pisteiden seuranta",
        "add_players": "Lisää pelaajat (vähintään 2)",
        "start_game": "Aloita peli",
        "name_prompt": "Syötä pelaajien nimet pilkuilla erotettuna",
        "round": "Kierros",
        "turn": " vuoro",
        "points_for": "Pisteet pelaajalle",
        "end_turn": "Lopeta vuoro",
        "undo": "Peruuta viimeisin vuoro",
        "scores": "Pisteet kierroksittain",
        "next_up": "Seuraavana",
        "press_enter": "Paina Enter lopettaaksesi vuoron",
        "total": "Yhteensä",
        "need_two": "Syötä vähintään kaksi pelaajaa.",
    },
}

TXT = TXT_DICT[st.session_state.lang]

# st.markdown(f"## {TXT['title']}")

# ---------------- Session state init ----------------
if "players" not in st.session_state:
    st.session_state.players = []
if "scores" not in st.session_state:
    st.session_state.scores = pd.DataFrame()
if "current_player_idx" not in st.session_state:
    st.session_state.current_player_idx = 0
if "round" not in st.session_state:
    st.session_state.round = 1
if "current_round_scores" not in st.session_state:
    st.session_state.current_round_scores = {}

# ---------------- Add players ----------------
if not st.session_state.players:
    st.subheader(TXT["add_players"])
    names = st.text_input(TXT["name_prompt"])
    if st.button(TXT["start_game"]):
        players = [p.strip() for p in names.split(",") if p.strip()]
        if len(players) < 2:
            st.error(TXT["need_two"])
        else:
            st.session_state.players = players
            st.session_state.scores = pd.DataFrame(
                columns=[TXT["round"]] + players
            )
            st.session_state.current_round_scores = {p: None for p in players}
            st.rerun()

# ---------------- Game screen ----------------
else:
    players = st.session_state.players
    i = st.session_state.current_player_idx
    cur = players[i]

    st.markdown(
        f"**{TXT['round']} {st.session_state.round} — {cur}{TXT['turn']}**"
    )

    # Layout: left for table, right for input + graph
    table_col, right_col = st.columns([2, 2])

    # ---------- Table on the left ----------
    live_row = {TXT["round"]: st.session_state.round}
    live_row.update(
        {p: st.session_state.current_round_scores[p] for p in players}
    )
    live_df = pd.concat(
        [st.session_state.scores, pd.DataFrame([live_row])], ignore_index=True
    )

    work_df = live_df.copy()
    for p in players:
        work_df[p] = pd.to_numeric(work_df[p], errors="coerce").fillna(0)

    totals = work_df[players].sum().astype(int).to_dict()

    display = live_df.copy()
    for p in players:
        display[p] = display[p].where(pd.notnull(display[p]), "")

    total_row = {TXT["round"]: TXT["total"]}
    total_row.update(totals)
    display_with_total = pd.concat(
        [display, pd.DataFrame([total_row])], ignore_index=True
    )

    with table_col:
        st.markdown(f"**{TXT['scores']}**")
        st.markdown(
            display_with_total.to_html(index=False), unsafe_allow_html=True
        )

    # ---------- Right column: input box + plot ----------
    with right_col:
        with st.form(key="turn_form", clear_on_submit=True):
            pts_str = st.text_input(f"{TXT['points_for']} {cur}", value="0")
            b1, b2 = st.columns(2)
            with b1:
                submitted = st.form_submit_button(TXT["end_turn"])
            with b2:
                undo_pressed = st.form_submit_button(TXT["undo"])

        # End Turn
        if submitted:
            try:
                pts = int(pts_str)
            except ValueError:
                pts = 0
            st.session_state.current_round_scores[cur] = pts

            if i == len(players) - 1:
                finalized = {TXT["round"]: st.session_state.round}
                finalized.update(
                    {
                        p: (st.session_state.current_round_scores[p] or 0)
                        for p in players
                    }
                )
                st.session_state.scores = pd.concat(
                    [st.session_state.scores, pd.DataFrame([finalized])],
                    ignore_index=True,
                )
                st.session_state.round += 1
                st.session_state.current_player_idx = 0
                st.session_state.current_round_scores = {
                    p: None for p in players
                }
            else:
                st.session_state.current_player_idx += 1

            st.rerun()

        # Undo
        if undo_pressed:
            filled_order = [
                p
                for p in players
                if st.session_state.current_round_scores.get(p) is not None
            ]
            if filled_order:
                last_p = filled_order[-1]
                st.session_state.current_round_scores[last_p] = None
                st.session_state.current_player_idx = players.index(last_p)
                st.rerun()

            if not st.session_state.scores.empty:
                last = st.session_state.scores.iloc[-1]
                st.session_state.scores = st.session_state.scores.iloc[
                    :-1
                ].reset_index(drop=True)
                st.session_state.round = int(last[TXT["round"]])
                st.session_state.current_round_scores = last.drop(
                    TXT["round"]
                ).to_dict()
                last_p = players[-1]
                st.session_state.current_round_scores[last_p] = None
                st.session_state.current_player_idx = len(players) - 1
                st.rerun()

        # Plot
        cumulative = work_df.copy()
        for p in players:
            cumulative[p] = cumulative[p].cumsum()
        present = live_df.copy()
        for p in players:
            present[p] = present[p].notna()

        melted_cum = cumulative.melt(
            id_vars=[TXT["round"]],
            value_vars=players,
            var_name="Player",
            value_name="Score",
        )
        melted_present = present.melt(
            id_vars=[TXT["round"]],
            value_vars=players,
            var_name="Player",
            value_name="Present",
        )
        plot_df = melted_cum.merge(melted_present, on=[TXT["round"], "Player"])
        plot_df = plot_df[plot_df["Present"] == True]

        fig = px.line(
            plot_df, x=TXT["round"], y="Score", color="Player", markers=True
        )
        fig.update_xaxes(tickmode="linear", dtick=1)  # whole number rounds
        fig.update_yaxes(rangemode="tozero")  # start from 0
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"{TXT['next_up']}: **{players[st.session_state.current_player_idx]}** — {TXT['press_enter']}"
    )

# Language selector at the bottom
lang_choice = st.selectbox(
    "Language / Kieli",
    ["Suomi", "English"],
    index=["Suomi", "English"].index(st.session_state.lang),
)
if lang_choice != st.session_state.lang:
    st.session_state.lang = lang_choice
    st.rerun()
