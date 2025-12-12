class NatalChart {
    constructor(elementId, size) {
        this.container = document.getElementById(elementId);
        this.size = size;
        this.cx = size / 2;
        this.cy = size / 2;
        this.ns = "http://www.w3.org/2000/svg";

        // Радиусы для одиночной карты
        this.rOuter = size / 2 - 5;
        this.rOuterAccent = this.rOuter - 15;
        this.rRulerOuter = this.rOuterAccent - 12;
        this.rRulerInner = this.rRulerOuter - 18;
        this.rZodiacOuter = this.rRulerInner - 12;
        this.rZodiacInner = this.rZodiacOuter - 35;
        this.rPlanetBase = this.rZodiacInner - 15;
        this.rAspect = this.rPlanetBase - 55;
        this.rHouseText = this.rAspect - 15;

        // Радиусы для двойной карты (транзиты снаружи)
        this.rOuterRing = size / 2 - 5;           // Внешний ореол
        this.rTransitOuter = this.rOuterRing - 10; // Внешнее кольцо транзитов
        this.rTransitInner = this.rTransitOuter - 40; // Внутренняя граница транзитов
        
        this.svg = document.createElementNS(this.ns, "svg");
        this.safeSetAttr(this.svg, "width", size);
        this.safeSetAttr(this.svg, "height", size);
        this.svg.style.background = "transparent";
        this.svg.style.display = "block";
        this.container.innerHTML = "";
        this.container.appendChild(this.svg);

        this.signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"];
        this.signColors = ["#f26d50","#4caf50","#ffeb3b","#26c6da",
                           "#ef5350","#66bb6a","#ffee58","#26c6da",
                           "#ef5350","#66bb6a","#ffee58","#26c6da"];
        this.glyphColors = {
            Sun: "#ff6d00",
            Moon: "#444",
            Mercury: "#111",
            Venus: "#4caf50",
            Mars: "#e53935",
            Jupiter: "#1565c0",
            Saturn: "#6d4c41",
            Uranus: "#00acc1",
            Neptune: "#3f51b5",
            Pluto: "#6a1b9a",
            North_node: "#000",
            South_node: "#000",
            Lilith: "#000",
            Chiron: "#7b1fa2",
            ASC: "#c62828",
            MC: "#1565c0"
        };
        
        this.planetIcons = {
            Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂",
            Jupiter: "♃", Saturn: "♄", Uranus: "♅", Neptune: "♆", Pluto: "♇",
            North_node: "☊", South_node: "☋", Lilith: "⚸", Chiron: "⚷",
            ASC: "AC", MC: "MC"
        };
    }

    draw(data) {
        if (!data || !data.houses || data.houses.length < 12) return;
        this.svg.innerHTML = "";
        this.rotationOffset = 180 - (data.houses[0] || 0);
        
        const hasOuter = data.outerPlanets && data.outerPlanets.length > 0;
        
        if (hasOuter) {
            this.drawDualChart(data);
        } else {
            this.drawSingleChart(data);
        }
    }

    // === SINGLE CHART (natal only) ===
    drawSingleChart(data) {
        this.drawBackground();
        this.drawOuterRuler();
        this.drawZodiacRing();
        this.drawHouses(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        if (data.planets) this.drawPlanets(data.planets);
        this.drawInnerCircle();
    }

    // === DUAL CHART (natal + transit/solar/lunar) ===
    drawDualChart(data) {
        // Пересчитываем радиусы для двойной карты
        const s = this.size;
        this.rOuter = s / 2 - 5;
        this.rTransitOuter = this.rOuter - 10;
        this.rTransitInner = this.rTransitOuter - 45;
        
        // Внутренняя натальная часть сжимается
        this.rOuterAccent = this.rTransitInner - 5;
        this.rRulerOuter = this.rOuterAccent - 8;
        this.rRulerInner = this.rRulerOuter - 12;
        this.rZodiacOuter = this.rRulerInner - 8;
        this.rZodiacInner = this.rZodiacOuter - 28;
        this.rPlanetBase = this.rZodiacInner - 12;
        this.rAspect = this.rPlanetBase - 40;
        this.rHouseText = this.rAspect - 10;

        // Рисуем
        this.drawDualBackground();
        this.drawOuterTransitRing(data.outerPlanets);
        this.drawOuterRuler();
        this.drawZodiacRing();
        this.drawHouses(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        if (data.planets) this.drawPlanets(data.planets);
        this.drawInnerCircle();
    }

    drawDualBackground() {
        // Внешний ореол (светло-бирюзовый для транзитов)
        const halo = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(halo, "cx", this.cx);
        this.safeSetAttr(halo, "cy", this.cy);
        this.safeSetAttr(halo, "r", this.rOuter);
        this.safeSetAttr(halo, "fill", "#e0f7fa");
        this.svg.appendChild(halo);

        // Кольцо транзитов
        const transitRing = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(transitRing, "cx", this.cx);
        this.safeSetAttr(transitRing, "cy", this.cy);
        this.safeSetAttr(transitRing, "r", this.rTransitOuter);
        this.safeSetAttr(transitRing, "fill", "#fff");
        this.safeSetAttr(transitRing, "stroke", "#4dd0e1");
        this.safeSetAttr(transitRing, "stroke-width", "2");
        this.svg.appendChild(transitRing);

        // Внутренний круг для натала
        const inner = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(inner, "cx", this.cx);
        this.safeSetAttr(inner, "cy", this.cy);
        this.safeSetAttr(inner, "r", this.rTransitInner);
        this.safeSetAttr(inner, "fill", "#e6f6d6");
        this.safeSetAttr(inner, "stroke", "#81c784");
        this.safeSetAttr(inner, "stroke-width", "1");
        this.svg.appendChild(inner);

        // Белый фон натала
        const white = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(white, "cx", this.cx);
        this.safeSetAttr(white, "cy", this.cy);
        this.safeSetAttr(white, "r", this.rOuterAccent);
        this.safeSetAttr(white, "fill", "#fff");
        this.safeSetAttr(white, "stroke", "#d1d5db");
        this.svg.appendChild(white);
    }

    drawOuterTransitRing(outerPlanets) {
        if (!outerPlanets || outerPlanets.length === 0) return;

        const midRadius = (this.rTransitOuter + this.rTransitInner) / 2;
        
        // Сортируем и распределяем планеты
        const sorted = [...outerPlanets].filter(p => p.abs_pos !== undefined);
        sorted.sort((a, b) => a.abs_pos - b.abs_pos);
        
        // Предотвращаем наложение
        const positions = this.spreadPlanets(sorted, 15);
        
        positions.forEach((p, i) => {
            const angle = this.toSvgAngle(p.displayPos);
            const pos = this.polarToCartesian(this.cx, this.cy, midRadius, angle);
            
            const icon = this.planetIcons[p.key] || p.icon || "?";
            const color = this.glyphColors[p.key] || "#e53935"; // Красный для транзитов
            
            // Символ планеты
            const text = document.createElementNS(this.ns, "text");
            this.safeSetAttr(text, "x", pos.x);
            this.safeSetAttr(text, "y", pos.y);
            this.safeSetAttr(text, "text-anchor", "middle");
            this.safeSetAttr(text, "dominant-baseline", "central");
            this.safeSetAttr(text, "font-size", "14");
            this.safeSetAttr(text, "font-weight", "bold");
            this.safeSetAttr(text, "fill", "#e53935");
            text.textContent = icon;
            this.svg.appendChild(text);
            
            // Ретроградность
            if (p.is_retro) {
                const retroPos = this.polarToCartesian(this.cx, this.cy, midRadius - 12, angle);
                const retro = document.createElementNS(this.ns, "text");
                this.safeSetAttr(retro, "x", retroPos.x);
                this.safeSetAttr(retro, "y", retroPos.y);
                this.safeSetAttr(retro, "text-anchor", "middle");
                this.safeSetAttr(retro, "dominant-baseline", "central");
                this.safeSetAttr(retro, "font-size", "8");
                this.safeSetAttr(retro, "fill", "#ff5555");
                retro.textContent = "R";
                this.svg.appendChild(retro);
            }

            // Линия к точной позиции
            const exactAngle = this.toSvgAngle(p.abs_pos);
            const outerPoint = this.polarToCartesian(this.cx, this.cy, this.rTransitOuter - 2, exactAngle);
            const innerPoint = this.polarToCartesian(this.cx, this.cy, this.rTransitInner + 2, exactAngle);
            
            const line = document.createElementNS(this.ns, "line");
            this.safeSetAttr(line, "x1", outerPoint.x);
            this.safeSetAttr(line, "y1", outerPoint.y);
            this.safeSetAttr(line, "x2", innerPoint.x);
            this.safeSetAttr(line, "y2", innerPoint.y);
            this.safeSetAttr(line, "stroke", "#e57373");
            this.safeSetAttr(line, "stroke-width", "1");
            this.svg.appendChild(line);
        });
    }

    spreadPlanets(planets, minGap) {
        // Создаём копии с displayPos
        const result = planets.map(p => ({ ...p, displayPos: p.abs_pos }));
        
        // Несколько проходов для разделения
        for (let pass = 0; pass < 5; pass++) {
            for (let i = 0; i < result.length; i++) {
                for (let j = i + 1; j < result.length; j++) {
                    let diff = result[j].displayPos - result[i].displayPos;
                    if (diff < 0) diff += 360;
                    if (diff > 180) diff = 360 - diff;
                    
                    if (diff < minGap) {
                        const push = (minGap - diff) / 2 + 1;
                        result[i].displayPos = (result[i].displayPos - push + 360) % 360;
                        result[j].displayPos = (result[j].displayPos + push) % 360;
                    }
                }
            }
        }
        return result;
    }

    safeSetAttr(el, name, val) {
        if (Number.isNaN(val) || val === undefined || val === null) return;
        el.setAttribute(name, val);
    }

    toSvgAngle(deg) {
        let chartDeg = deg + this.rotationOffset;
        chartDeg = chartDeg % 360;
        if (chartDeg < 0) chartDeg += 360;
        return -chartDeg; 
    }

    drawBackground() {
        const halo = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(halo, "cx", this.cx);
        this.safeSetAttr(halo, "cy", this.cy);
        this.safeSetAttr(halo, "r", this.rOuter);
        this.safeSetAttr(halo, "fill", "#e6f6d6");
        this.svg.appendChild(halo);

        const white = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(white, "cx", this.cx);
        this.safeSetAttr(white, "cy", this.cy);
        this.safeSetAttr(white, "r", this.rOuterAccent);
        this.safeSetAttr(white, "fill", "#fff");
        this.safeSetAttr(white, "stroke", "#d1d5db");
        this.svg.appendChild(white);
    }

    drawOuterRuler() {
        for (let deg = 0; deg < 360; deg++) {
            const angle = this.toSvgAngle(deg);
            let len = 4;
            if (deg % 5 === 0) len = 7;
            if (deg % 10 === 0) len = 12;
            if (deg % 30 === 0) len = 18;

            const p1 = this.polarToCartesian(this.cx, this.cy, this.rRulerOuter, angle);
            const p2 = this.polarToCartesian(this.cx, this.cy, this.rRulerOuter - len, angle);
            const tick = document.createElementNS(this.ns, "line");
            this.safeSetAttr(tick, "x1", p1.x);
            this.safeSetAttr(tick, "y1", p1.y);
            this.safeSetAttr(tick, "x2", p2.x);
            this.safeSetAttr(tick, "y2", p2.y);
            this.safeSetAttr(tick, "stroke", "#555");
            this.safeSetAttr(tick, "stroke-width", deg % 30 === 0 ? 1.2 : 0.5);
            this.svg.appendChild(tick);
        }
    }

    drawZodiacRing() {
        for (let i = 0; i < 12; i++) {
            const start = i * 30;
            const end = start + 30;
            const sector = this.createSector(this.cx, this.cy, this.rZodiacOuter, this.rZodiacInner, this.toSvgAngle(start), this.toSvgAngle(end));
            this.safeSetAttr(sector, "fill", this.signColors[i]);
            this.safeSetAttr(sector, "stroke", "#999");
            this.safeSetAttr(sector, "stroke-width", "0.6");
            this.svg.appendChild(sector);

            const mid = start + 15;
            const textPos = this.polarToCartesian(this.cx, this.cy, (this.rZodiacOuter + this.rZodiacInner) / 2, this.toSvgAngle(mid));
            const glyph = document.createElementNS(this.ns, "text");
            this.safeSetAttr(glyph, "x", textPos.x);
            this.safeSetAttr(glyph, "y", textPos.y);
            this.safeSetAttr(glyph, "text-anchor", "middle");
            this.safeSetAttr(glyph, "dominant-baseline", "central");
            this.safeSetAttr(glyph, "font-size", "16");
            this.safeSetAttr(glyph, "font-weight", "bold");
            glyph.textContent = this.signs[i];
            this.svg.appendChild(glyph);
        }
    }

    drawHouses(cusps) {
        cusps.forEach((deg, i) => {
            const angle = this.toSvgAngle(deg);
            const outer = this.polarToCartesian(this.cx, this.cy, this.rRulerOuter - 8, angle);
            const inner = this.polarToCartesian(this.cx, this.cy, this.rAspect, angle);
            const line = document.createElementNS(this.ns, "line");
            this.safeSetAttr(line, "x1", outer.x);
            this.safeSetAttr(line, "y1", outer.y);
            this.safeSetAttr(line, "x2", inner.x);
            this.safeSetAttr(line, "y2", inner.y);
            let color = "#444";
            let width = "1";
            if ([0,3,6,9].includes(i)) {
                width = "2";
                color = "#002e8a";
            }
            this.safeSetAttr(line, "stroke", color);
            this.safeSetAttr(line, "stroke-width", width);
            this.svg.appendChild(line);

            const next = cusps[(i+1)%12];
            let mid = (deg + next) / 2;
            if (Math.abs(next - deg) > 180) mid += 180;
            const labelPos = this.polarToCartesian(this.cx, this.cy, this.rHouseText, this.toSvgAngle(mid));
            const txt = document.createElementNS(this.ns, "text");
            this.safeSetAttr(txt, "x", labelPos.x);
            this.safeSetAttr(txt, "y", labelPos.y);
            this.safeSetAttr(txt, "text-anchor", "middle");
            this.safeSetAttr(txt, "dominant-baseline", "central");
            this.safeSetAttr(txt, "font-size", "10");
            this.safeSetAttr(txt, "fill", "#666");
            txt.textContent = i + 1;
            this.svg.appendChild(txt);
        });
    }

    drawAspects(aspects, planets) {
        const planetMap = {};
        planets.forEach(p => { if (p.key) planetMap[p.key] = p; });

        const colors = {
            Conjunction: "#29b6f6",
            Sextile: "#4caf50",
            Square: "#ff5252",
            Trine: "#4caf50",
            Opposition: "#ff9800",
            Quincunx: "#26c6da"
        };

        aspects.forEach(a => {
            const p1 = planetMap[a.p1_key];
            const p2 = planetMap[a.p2_key];
            if (!p1 || !p2) return;

            const angle1 = this.toSvgAngle(p1.abs_pos);
            const angle2 = this.toSvgAngle(p2.abs_pos);
            const point1 = this.polarToCartesian(this.cx, this.cy, this.rAspect, angle1);
            const point2 = this.polarToCartesian(this.cx, this.cy, this.rAspect, angle2);

            const line = document.createElementNS(this.ns, "line");
            this.safeSetAttr(line, "x1", point1.x);
            this.safeSetAttr(line, "y1", point1.y);
            this.safeSetAttr(line, "x2", point2.x);
            this.safeSetAttr(line, "y2", point2.y);
            this.safeSetAttr(line, "stroke", colors[a.type] || "#888");
            this.safeSetAttr(line, "stroke-width", "1.2");
            this.safeSetAttr(line, "opacity", "0.7");
            this.svg.appendChild(line);
        });
    }

    drawPlanets(planets) {
        const sorted = [...planets].filter(p => p.abs_pos !== undefined);
        sorted.sort((a, b) => a.abs_pos - b.abs_pos);
        
        const positions = this.spreadPlanets(sorted, 12);

        positions.forEach(p => {
            const angle = this.toSvgAngle(p.displayPos);
            const pos = this.polarToCartesian(this.cx, this.cy, this.rPlanetBase, angle);

            const icon = this.planetIcons[p.key] || p.icon || "?";
            const color = this.glyphColors[p.key] || "#333";

            // Background circle
            const bg = document.createElementNS(this.ns, "circle");
            this.safeSetAttr(bg, "cx", pos.x);
            this.safeSetAttr(bg, "cy", pos.y);
            this.safeSetAttr(bg, "r", 10);
            this.safeSetAttr(bg, "fill", "#fff");
            this.svg.appendChild(bg);

            // Planet symbol
            const text = document.createElementNS(this.ns, "text");
            this.safeSetAttr(text, "x", pos.x);
            this.safeSetAttr(text, "y", pos.y);
            this.safeSetAttr(text, "text-anchor", "middle");
            this.safeSetAttr(text, "dominant-baseline", "central");
            this.safeSetAttr(text, "font-size", p.key === 'ASC' || p.key === 'MC' ? "9" : "14");
            this.safeSetAttr(text, "font-weight", "bold");
            this.safeSetAttr(text, "fill", color);
            text.textContent = icon;
            this.svg.appendChild(text);

            // Retrograde marker
            if (p.is_retro) {
                const retroPos = this.polarToCartesian(this.cx, this.cy, this.rPlanetBase - 14, angle);
                const retro = document.createElementNS(this.ns, "text");
                this.safeSetAttr(retro, "x", retroPos.x);
                this.safeSetAttr(retro, "y", retroPos.y);
                this.safeSetAttr(retro, "text-anchor", "middle");
                this.safeSetAttr(retro, "dominant-baseline", "central");
                this.safeSetAttr(retro, "font-size", "8");
                this.safeSetAttr(retro, "fill", "#ff5555");
                retro.textContent = "R";
                this.svg.appendChild(retro);
            }

            // Line to exact position
            const exactAngle = this.toSvgAngle(p.abs_pos);
            const outerPoint = this.polarToCartesian(this.cx, this.cy, this.rZodiacInner - 2, exactAngle);
            const innerPoint = this.polarToCartesian(this.cx, this.cy, this.rPlanetBase + 12, exactAngle);
            
            const line = document.createElementNS(this.ns, "line");
            this.safeSetAttr(line, "x1", outerPoint.x);
            this.safeSetAttr(line, "y1", outerPoint.y);
            this.safeSetAttr(line, "x2", innerPoint.x);
            this.safeSetAttr(line, "y2", innerPoint.y);
            this.safeSetAttr(line, "stroke", "#666");
            this.safeSetAttr(line, "stroke-width", "1");
            this.svg.appendChild(line);

            // Degree label
            const degPos = this.polarToCartesian(this.cx, this.cy, this.rPlanetBase - 22, angle);
            const degText = document.createElementNS(this.ns, "text");
            this.safeSetAttr(degText, "x", degPos.x);
            this.safeSetAttr(degText, "y", degPos.y);
            this.safeSetAttr(degText, "text-anchor", "middle");
            this.safeSetAttr(degText, "dominant-baseline", "central");
            this.safeSetAttr(degText, "font-size", "8");
            this.safeSetAttr(degText, "fill", "#666");
            degText.textContent = Math.floor(p.pos) + "°";
            this.svg.appendChild(degText);
        });
    }

    drawInnerCircle() {
        const inner = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(inner, "cx", this.cx);
        this.safeSetAttr(inner, "cy", this.cy);
        this.safeSetAttr(inner, "r", this.rAspect);
        this.safeSetAttr(inner, "fill", "none");
        this.safeSetAttr(inner, "stroke", "#aaa");
        this.safeSetAttr(inner, "stroke-width", "1");
        this.svg.appendChild(inner);
    }

    createSector(cx, cy, rOuter, rInner, startAngle, endAngle) {
        const rad = Math.PI / 180;
        const x1o = cx + rOuter * Math.cos(startAngle * rad);
        const y1o = cy - rOuter * Math.sin(startAngle * rad);
        const x2o = cx + rOuter * Math.cos(endAngle * rad);
        const y2o = cy - rOuter * Math.sin(endAngle * rad);
        const x1i = cx + rInner * Math.cos(endAngle * rad);
        const y1i = cy - rInner * Math.sin(endAngle * rad);
        const x2i = cx + rInner * Math.cos(startAngle * rad);
        const y2i = cy - rInner * Math.sin(startAngle * rad);

        const largeArc = Math.abs(endAngle - startAngle) > 180 ? 1 : 0;
        const sweep = endAngle > startAngle ? 0 : 1;

        const d = [
            `M ${x1o} ${y1o}`,
            `A ${rOuter} ${rOuter} 0 ${largeArc} ${sweep} ${x2o} ${y2o}`,
            `L ${x1i} ${y1i}`,
            `A ${rInner} ${rInner} 0 ${largeArc} ${1-sweep} ${x2i} ${y2i}`,
            `Z`
        ].join(" ");

        const path = document.createElementNS(this.ns, "path");
        path.setAttribute("d", d);
        return path;
    }

    polarToCartesian(cx, cy, r, angleDeg) {
        const rad = angleDeg * Math.PI / 180;
        return {
            x: cx + r * Math.cos(rad),
            y: cy - r * Math.sin(rad)
        };
    }
}

