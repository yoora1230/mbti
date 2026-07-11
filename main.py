from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import pycountry
import streamlit as st


# ---------------------------------------------------------
# 페이지 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="MBTI 세계 탐험대",
    page_icon="🌍",
    layout="wide",
)

MBTI_TYPES = [
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ",
]

MBTI_EMOJI = {
    "ISTJ": "📋", "ISFJ": "🤝", "INFJ": "🔮", "INTJ": "♟️",
    "ISTP": "🛠️", "ISFP": "🎨", "INFP": "🌱", "INTP": "🧠",
    "ESTP": "🏄", "ESFP": "🎉", "ENFP": "✨", "ENTP": "💡",
    "ESTJ": "📣", "ESFJ": "💛", "ENFJ": "🌟", "ENTJ": "🚀",
}

# pycountry에서 바로 찾기 어려운 국가 이름만 보정합니다.
ISO3_OVERRIDES = {
    "Bolivia": "BOL",
    "Brunei": "BRN",
    "Congo": "COG",
    "Congo (Kinshasa)": "COD",
    "Czech Republic": "CZE",
    "Iran": "IRN",
    "Laos": "LAO",
    "Macedonia": "MKD",
    "Moldova": "MDA",
    "Russia": "RUS",
    "South Korea": "KOR",
    "Syria": "SYR",
    "Tanzania": "TZA",
    "Venezuela": "VEN",
    "Vietnam": "VNM",
}

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            padding: 2rem 2.2rem;
            border-radius: 24px;
            background: linear-gradient(135deg, #eef2ff 0%, #ecfeff 55%, #f0fdf4 100%);
            border: 1px solid rgba(99, 102, 241, 0.16);
            margin-bottom: 1.2rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.45rem;
            letter-spacing: -0.04em;
        }
        .hero p {
            margin: 0.7rem 0 0 0;
            color: #475569;
            font-size: 1.05rem;
        }
        .result-card {
            padding: 1.35rem;
            border-radius: 18px;
            background: white;
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            min-height: 145px;
        }
        .result-label {
            color: #64748b;
            font-size: 0.88rem;
            margin-bottom: 0.35rem;
        }
        .result-value {
            font-size: 1.55rem;
            font-weight: 800;
            color: #0f172a;
        }
        .result-sub {
            color: #64748b;
            font-size: 0.88rem;
            margin-top: 0.35rem;
        }
        [data-testid="stSidebar"] {
            background-color: #f8fafc;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 데이터 불러오기 및 검사
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """main.py와 같은 폴더의 CSV 파일을 읽고 검사합니다."""
    csv_path = Path(__file__).with_name("countriesMBTI_16types.csv")

    if not csv_path.exists():
        raise FileNotFoundError(
            "countriesMBTI_16types.csv 파일을 main.py와 같은 폴더에 넣어 주세요."
        )

    data = pd.read_csv(csv_path)
    data.columns = data.columns.astype(str).str.strip()

    required_columns = {"Country", *MBTI_TYPES}
    missing_columns = sorted(required_columns - set(data.columns))
    if missing_columns:
        raise ValueError(
            "CSV에 필요한 열이 없습니다: " + ", ".join(missing_columns)
        )

    data = data[["Country", *MBTI_TYPES]].copy()
    data["Country"] = data["Country"].astype(str).str.strip()

    if data["Country"].eq("").any():
        raise ValueError("Country 열에 빈 국가 이름이 있습니다.")

    for mbti in MBTI_TYPES:
        data[mbti] = pd.to_numeric(data[mbti], errors="coerce")

    if data[MBTI_TYPES].isna().any().any():
        raise ValueError("MBTI 비율 열에 숫자가 아닌 값 또는 빈칸이 있습니다.")

    # 현재 데이터는 0~1 사이의 비율입니다. 0~100 데이터가 들어오면 자동 변환합니다.
    if data[MBTI_TYPES].to_numpy().max() > 1:
        data[MBTI_TYPES] = data[MBTI_TYPES] / 100

    return data


def country_to_iso3(country_name: str) -> Optional[str]:
    """국가 이름을 세계 지도용 ISO-3 코드로 변환합니다."""
    if country_name in ISO3_OVERRIDES:
        return ISO3_OVERRIDES[country_name]

    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except LookupError:
        return None


try:
    df = load_data()
except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
    st.error(f"데이터를 불러오지 못했습니다.\n\n{error}")
    st.info(
        "GitHub 저장소의 같은 위치에 main.py, requirements.txt, "
        "countriesMBTI_16types.csv 파일을 함께 올려 주세요."
    )
    st.stop()


# ---------------------------------------------------------
# 제목 및 사이드바
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🌍 MBTI 세계 탐험대</h1>
        <p>나와 같은 MBTI 유형의 비율이 높은 나라를 찾아보세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("🔎 탐색 설정")

    selected_mbti = st.selectbox(
        "나의 MBTI",
        MBTI_TYPES,
        index=MBTI_TYPES.index("INFP"),
    )

    top_n = st.slider(
        "순위에 표시할 국가 수",
        min_value=5,
        max_value=min(30, len(df)),
        value=min(10, len(df)),
        step=1,
    )

    st.divider()
    st.caption(
        "이 사이트의 수치는 각 나라에서 해당 MBTI가 차지하는 비율입니다. "
        "국가의 전체 인구를 반영한 실제 인원수 순위는 아닙니다."
    )


# ---------------------------------------------------------
# 선택한 MBTI 결과 계산
# ---------------------------------------------------------
ranking = (
    df[["Country", selected_mbti]]
    .rename(columns={selected_mbti: "Ratio"})
    .sort_values("Ratio", ascending=False)
    .reset_index(drop=True)
)
ranking["Rank"] = ranking.index + 1
ranking["Percent"] = ranking["Ratio"] * 100

best = ranking.iloc[0]
average_percent = ranking["Percent"].mean()
median_percent = ranking["Percent"].median()

korea_match = ranking.loc[ranking["Country"] == "South Korea"]
if korea_match.empty:
    korea_rank_text = "데이터 없음"
    korea_percent_text = "한국 행을 찾지 못했어요"
else:
    korea_rank = int(korea_match.iloc[0]["Rank"])
    korea_percent = float(korea_match.iloc[0]["Percent"])
    korea_rank_text = f"{korea_rank}위"
    korea_percent_text = f"{korea_percent:.2f}%"

st.subheader(f"{MBTI_EMOJI[selected_mbti]} {selected_mbti} 결과")

card1, card2, card3, card4 = st.columns(4)
with card1:
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">가장 비율이 높은 나라</div>
            <div class="result-value">🥇 {best['Country']}</div>
            <div class="result-sub">{best['Percent']:.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with card2:
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">전체 국가 평균</div>
            <div class="result-value">{average_percent:.2f}%</div>
            <div class="result-sub">{len(ranking)}개 국가 기준</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with card3:
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">중앙값</div>
            <div class="result-value">{median_percent:.2f}%</div>
            <div class="result-sub">국가별 비율의 가운데 값</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with card4:
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">대한민국 순위</div>
            <div class="result-value">🇰🇷 {korea_rank_text}</div>
            <div class="result-sub">{korea_percent_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# 탭은 보이지 않는 내용도 모두 계산하므로, 라디오 버튼으로 선택한 화면만 렌더링합니다.
view = st.radio(
    "보기 선택",
    ["🏆 국가 순위", "🗺️ 세계 지도", "📊 나라 비교", "📄 전체 데이터"],
    horizontal=True,
    label_visibility="collapsed",
)


# ---------------------------------------------------------
# 국가 순위
# ---------------------------------------------------------
if view == "🏆 국가 순위":
    top_df = ranking.head(top_n).sort_values("Percent", ascending=True)

    bar_fig = px.bar(
        top_df,
        x="Percent",
        y="Country",
        orientation="h",
        text="Percent",
        labels={"Percent": "비율(%)", "Country": "국가"},
        title=f"{selected_mbti} 비율 상위 {top_n}개 나라",
        color="Percent",
        color_continuous_scale="Blues",
    )
    bar_fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>비율: %{x:.2f}%<extra></extra>",
    )
    bar_fig.update_layout(
        height=max(470, top_n * 34),
        coloraxis_showscale=False,
        margin=dict(l=10, r=30, t=60, b=10),
        yaxis_title=None,
    )
    st.plotly_chart(
        bar_fig,
        width="stretch",
        config={"displaylogo": False},
    )

    rank_table = ranking.head(top_n)[["Rank", "Country", "Percent"]].copy()
    rank_table.columns = ["순위", "국가", f"{selected_mbti} 비율(%)"]

    st.dataframe(
        rank_table,
        hide_index=True,
        width="stretch",
        column_config={
            "순위": st.column_config.NumberColumn(format="%d위"),
            f"{selected_mbti} 비율(%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    download_data = ranking[["Rank", "Country", "Percent"]].copy()
    download_data.columns = ["Rank", "Country", f"{selected_mbti}_Percent"]
    st.download_button(
        label=f"⬇️ {selected_mbti} 전체 순위 CSV 다운로드",
        data=download_data.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{selected_mbti}_country_ranking.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------
# 세계 지도
# ---------------------------------------------------------
elif view == "🗺️ 세계 지도":
    with st.spinner("세계 지도를 준비하고 있습니다..."):
        map_df = ranking.copy()
        map_df["ISO3"] = map_df["Country"].map(country_to_iso3)
        unmapped = map_df.loc[map_df["ISO3"].isna(), "Country"].tolist()
        map_df = map_df.dropna(subset=["ISO3"])

        map_fig = px.choropleth(
            map_df,
            locations="ISO3",
            color="Percent",
            hover_name="Country",
            hover_data={"ISO3": False, "Percent": ":.2f"},
            color_continuous_scale="Viridis",
            labels={"Percent": f"{selected_mbti} 비율(%)"},
            title=f"세계의 {selected_mbti} 비율",
        )
        map_fig.update_geos(
            showcoastlines=True,
            coastlinecolor="#94a3b8",
            showland=True,
            landcolor="#f1f5f9",
            showframe=False,
            projection_type="natural earth",
        )
        map_fig.update_layout(
            height=620,
            margin=dict(l=0, r=0, t=60, b=0),
        )

    st.plotly_chart(
        map_fig,
        width="stretch",
        config={"displaylogo": False},
    )

    if unmapped:
        st.caption("지도에 표시되지 않은 국가: " + ", ".join(unmapped))


# ---------------------------------------------------------
# 나라 비교
# ---------------------------------------------------------
elif view == "📊 나라 비교":
    default_countries = [
        country
        for country in ["South Korea", "Japan", "United States", "United Kingdom"]
        if country in df["Country"].values
    ]

    selected_countries = st.multiselect(
        "비교할 나라를 선택하세요",
        options=sorted(df["Country"].tolist()),
        default=default_countries,
        max_selections=8,
    )

    if not selected_countries:
        st.info("비교할 나라를 한 곳 이상 선택해 주세요.")
    else:
        compare_df = ranking[ranking["Country"].isin(selected_countries)].copy()
        compare_df = compare_df.sort_values("Percent", ascending=False)

        compare_fig = px.bar(
            compare_df,
            x="Country",
            y="Percent",
            text="Percent",
            labels={"Country": "국가", "Percent": "비율(%)"},
            title=f"선택한 나라의 {selected_mbti} 비율 비교",
            color="Country",
        )
        compare_fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>비율: %{y:.2f}%<extra></extra>",
        )
        compare_fig.update_layout(
            height=500,
            showlegend=False,
            margin=dict(l=10, r=10, t=60, b=10),
        )
        st.plotly_chart(
            compare_fig,
            width="stretch",
            config={"displaylogo": False},
        )

        compare_table = compare_df[["Rank", "Country", "Percent"]].copy()
        compare_table.columns = ["세계 순위", "국가", f"{selected_mbti} 비율(%)"]
        st.dataframe(
            compare_table,
            hide_index=True,
            width="stretch",
            column_config={
                "세계 순위": st.column_config.NumberColumn(format="%d위"),
                f"{selected_mbti} 비율(%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )


# ---------------------------------------------------------
# 전체 데이터
# ---------------------------------------------------------
else:
    search_country = st.text_input(
        "국가 이름 검색",
        placeholder="예: Korea, Japan, Canada",
    )

    display_df = df.copy()
    if search_country.strip():
        display_df = display_df[
            display_df["Country"].str.contains(
                search_country.strip(), case=False, na=False
            )
        ]

    percent_df = display_df.copy()
    percent_df[MBTI_TYPES] = percent_df[MBTI_TYPES] * 100

    st.dataframe(
        percent_df,
        hide_index=True,
        width="stretch",
        column_config={
            mbti: st.column_config.NumberColumn(format="%.2f%%")
            for mbti in MBTI_TYPES
        },
    )

    st.caption(
        f"현재 {len(display_df)}개 국가를 표시하고 있습니다. "
        "표의 MBTI 값은 보기 쉽게 백분율로 변환했습니다."
    )

st.divider()
st.caption(
    "💡 해석할 때 주의: 이 데이터는 국가별 MBTI 비율 데이터이며, "
    "MBTI는 사람의 성격 전체를 완전히 설명하는 절대적인 기준은 아닙니다."
)
