class NatalChart {
    constructor(elementId, size) {
        this.container = document.getElementById(elementId);
        this.size = size;
        this.cx = size / 2;
        this.cy = size / 2;
        this.ns = "http://www.w3.org/2000/svg";

        // Радиусы (приближены к геокуптовскому стилю)
        this.rOuter = size / 2 - 5;            // Зеленый ореол
        this.rOuterAccent = this.rOuter - 15;  // Белый внешний круг
        this.rRulerOuter = this.rOuterAccent - 12;
        this.rRulerInner = this.rRulerOuter - 18;
        this.rZodiacOuter = this.rRulerInner - 12;
        this.rZodiacInner = this.rZodiacOuter - 35;
        this.rPlanetBase = this.rZodiacInner - 15;
        this.rAspect = this.rPlanetBase - 55;
        this.rHouseText = this.rAspect - 15;

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
            Lilith: "#000"
        };
    }

    draw(data) {
        if (!data || !data.houses || data.houses.length < 12) return;
        this.svg.innerHTML = "";
        this.rotationOffset = 180 - (data.houses[0] || 0);

        this.drawBackground();
        this.drawOuterRuler();
        this.drawZodiacRing();
        this.drawHouses(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        if (data.planets) this.drawPlanets(data.planets);
        this.drawInnerCircle();
    }

    safeSetAttr(el, name, val) {
        if (Number.isNaN(val) || val === undefined || val === null) return;
        el.setAttribute(name, val);
    }

    // Converts absolute zodiac degree (0=0 Ari) to SVG angle
    // 0 deg Ari in SVG is usually 0 radians (Right).
    // We apply rotationOffset.
    // Also SVG coordinates: 0 angle is 3 o'clock. Astronomy usually counts CCW.
    toSvgAngle(deg) {
        // Astrology: 0 is Aries. In our chart with rotation:
        // displayAngle = deg + rotationOffset
        // But SVG 0 is 3 o'clock.
        // We want Aries 0 to be at (180 - rotationOffset)? 
        // Let's simplify:
        // We rotate the whole canvas logic by adding rotationOffset to the degree.
        // Then we convert to SVG angle. SVG angle 0 is East.
        // Astrology 0 (Aries) usually starts at East if no rotation.
        // So: svgAngle = - (deg + offset). Why minus? Because SVG Y is down.
        
        // Let's stick to: 
        // Angle in degrees CCW from East (3 o'clock).
        let chartDeg = deg + this.rotationOffset;
        // Correct to 0-360
        chartDeg = chartDeg % 360;
        if (chartDeg < 0) chartDeg += 360;
        
        // In SVG geometry: x = r*cos(a), y = r*sin(a).
        // But 'a' increases CW if Y is down? No, standard Math.cos is CCW if Y is up.
        // With Y down: increasing angle goes CW visually on screen (if X right, Y down).
        // Astrology counts CCW.
        // So we need to negate the angle for SVG math.
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
            let len = 6;
            if (deg % 5 === 0) len = 10;
            if (deg % 10 === 0) len = 16;
            if (deg % 30 === 0) len = 22;

            const p1 = this.polarToCartesian(this.cx, this.cy, this.rRulerOuter, angle);
            const p2 = this.polarToCartesian(this.cx, this.cy, this.rRulerOuter - len, angle);
            const tick = document.createElementNS(this.ns, "line");
            this.safeSetAttr(tick, "x1", p1.x);
            this.safeSetAttr(tick, "y1", p1.y);
            this.safeSetAttr(tick, "x2", p2.x);
            this.safeSetAttr(tick, "y2", p2.y);
            this.safeSetAttr(tick, "stroke", "#555");
            this.safeSetAttr(tick, "stroke-width", deg % 30 === 0 ? 1.3 : 0.6);
            this.svg.appendChild(tick);

            if (deg % 30 === 0) {
                const label = document.createElementNS(this.ns, "text");
                const textPos = this.polarToCartesian(this.cx, this.cy, this.rRulerOuter - 30, angle);
                this.safeSetAttr(label, "x", textPos.x);
                this.safeSetAttr(label, "y", textPos.y);
                this.safeSetAttr(label, "text-anchor", "middle");
                this.safeSetAttr(label, "dominant-baseline", "central");
                this.safeSetAttr(label, "font-size", "9");
                this.safeSetAttr(label, "fill", "#666");
                label.textContent = deg;
                this.svg.appendChild(label);
            }
        }
    }

    drawZodiacRing() {
        for (let i = 0; i < 12; i++) {
            const start = i * 30;
            const end = start + 30;
            const sector = this.createSector(this.cx, this.cy, this.rZodiacOuter, this.rZodiacInner, this.toSvgAngle(start), this.toSvgAngle(end));
            this.safeSetAttr(sector, "fill", this.signColors[i]);
            this.safeSetAttr(sector, "stroke", "#999");
            this.safeSetAttr(sector, "stroke-width", "0.8");
            this.svg.appendChild(sector);

            const mid = start + 15;
            const textPos = this.polarToCartesian(this.cx, this.cy, (this.rZodiacOuter + this.rZodiacInner) / 2, this.toSvgAngle(mid));
            const glyph = document.createElementNS(this.ns, "text");
            this.safeSetAttr(glyph, "x", textPos.x);
            this.safeSetAttr(glyph, "y", textPos.y);
            this.safeSetAttr(glyph, "text-anchor", "middle");
            this.safeSetAttr(glyph, "dominant-baseline", "central");
            this.safeSetAttr(glyph, "font-size", "20");
            this.safeSetAttr(glyph, "font-weight", "bold");
            glyph.textContent = this.signs[i];
            this.svg.appendChild(glyph);
        }
    }

    drawHouses(cusps) {
        cusps.forEach((deg, i) => {
            const angle = this.toSvgAngle(deg);
            const outer = this.polarToCartesian(this.cx, this.cy, this.rRulerOuter - 10, angle);
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
            this.safeSetAttr(txt, "font-size", "11");
            this.safeSetAttr(txt, "fill", "#555");
            txt.textContent = i + 1;
            this.svg.appendChild(txt);
        });
    }

    drawPlanets(planets) {
        const filtered = planets
            .filter(p => p.key !== "ASC" && p.key !== "MC")
            .sort((a, b) => a.abs_pos - b.abs_pos);

        const layers = new Array(filtered.length).fill(0);
        const threshold = 7; // degrees to consider overlapping

        filtered.forEach((planet, idx) => {
            let layer = 0;
            for (let j = 0; j < idx; j++) {
                const other = filtered[j];
                let diff = Math.abs(planet.abs_pos - other.abs_pos);
                if (diff > 180) diff = 360 - diff;
                if (diff < threshold) {
                    layer = Math.max(layer, layers[j] + 1);
                }
            }
            layers[idx] = layer;

            const angle = this.toSvgAngle(planet.abs_pos);
            const radius = Math.max(this.rAspect + 25, this.rPlanetBase - layer * 18);

            const glyphPos = this.polarToCartesian(this.cx, this.cy, radius, angle);
            const tickStart = this.polarToCartesian(this.cx, this.cy, this.rZodiacInner - 4, angle);
            const connector = document.createElementNS(this.ns, "line");
            this.safeSetAttr(connector, "x1", tickStart.x);
            this.safeSetAttr(connector, "y1", tickStart.y);
            this.safeSetAttr(connector, "x2", glyphPos.x);
            this.safeSetAttr(connector, "y2", glyphPos.y);
            this.safeSetAttr(connector, "stroke", "#b0bec5");
            this.safeSetAttr(connector, "stroke-width", "1");
            this.svg.appendChild(connector);

            const glyph = document.createElementNS(this.ns, "text");
            this.safeSetAttr(glyph, "x", glyphPos.x);
            this.safeSetAttr(glyph, "y", glyphPos.y);
            this.safeSetAttr(glyph, "text-anchor", "middle");
            this.safeSetAttr(glyph, "dominant-baseline", "central");
            this.safeSetAttr(glyph, "font-size", "18");
            this.safeSetAttr(glyph, "font-weight", "bold");
            this.safeSetAttr(glyph, "fill", this.glyphColors[planet.key] || "#111");
            glyph.textContent = planet.icon;
            this.svg.appendChild(glyph);

            if (planet.is_retro) {
                const rText = document.createElementNS(this.ns, "text");
                const retroPos = this.polarToCartesian(this.cx, this.cy, radius - 10, angle - 12);
                this.safeSetAttr(rText, "x", retroPos.x);
                this.safeSetAttr(rText, "y", retroPos.y);
                this.safeSetAttr(rText, "font-size", "9");
                this.safeSetAttr(rText, "fill", "#d32f2f");
                rText.textContent = "R";
                this.svg.appendChild(rText);
            }

            const degText = document.createElementNS(this.ns, "text");
            const degPos = this.polarToCartesian(this.cx, this.cy, radius + 20, angle);
            this.safeSetAttr(degText, "x", degPos.x);
            this.safeSetAttr(degText, "y", degPos.y);
            this.safeSetAttr(degText, "text-anchor", "middle");
            this.safeSetAttr(degText, "font-size", "9");
            this.safeSetAttr(degText, "fill", "#263238");
            const minutes = Math.round((planet.pos % 1) * 60);
            degText.textContent = `${Math.floor(planet.pos)}°${minutes.toString().padStart(2, "0")}`;
            this.svg.appendChild(degText);
        });
    }

    drawAspects(aspects, planets) {
        const map = {};
        planets.forEach(p => map[p.name] = p.abs_pos);

        const style = {
            Opposition: { color: "#ff5252", width: 2 },
            Square: { color: "#ff5252", width: 1.8 },
            Trine: { color: "#4caf50", width: 1.5 },
            Sextile: { color: "#29b6f6", width: 1.3, dash: "6 4" },
            Conjunction: { color: "#ff9800", width: 1.8 }
        };

        aspects.forEach(aspect => {
            const d1 = map[aspect.p1];
            const d2 = map[aspect.p2];
            if (d1 === undefined || d2 === undefined) return;

            const p1 = this.polarToCartesian(this.cx, this.cy, this.rAspect, this.toSvgAngle(d1));
            const p2 = this.polarToCartesian(this.cx, this.cy, this.rAspect, this.toSvgAngle(d2));
            const line = document.createElementNS(this.ns, "line");
            const conf = style[aspect.type] || { color: "#b0bec5", width: 1 };

            this.safeSetAttr(line, "x1", p1.x);
            this.safeSetAttr(line, "y1", p1.y);
            this.safeSetAttr(line, "x2", p2.x);
            this.safeSetAttr(line, "y2", p2.y);
            this.safeSetAttr(line, "stroke", conf.color);
            this.safeSetAttr(line, "stroke-width", conf.width);
            this.safeSetAttr(line, "stroke-linecap", "round");
            if (conf.dash) this.safeSetAttr(line, "stroke-dasharray", conf.dash);
            this.svg.appendChild(line);
        });
    }

    drawInnerCircle() {
        const inner = document.createElementNS(this.ns, "circle");
        this.safeSetAttr(inner, "cx", this.cx);
        this.safeSetAttr(inner, "cy", this.cy);
        this.safeSetAttr(inner, "r", this.rAspect);
        this.safeSetAttr(inner, "fill", "none");
        this.safeSetAttr(inner, "stroke", "#b0bec5");
        inner.setAttribute("stroke-dasharray", "4 6");
        this.svg.appendChild(inner);
    }

    polarToCartesian(centerX, centerY, radius, angleInDegrees) {
        // SVG standard: angle 0 is 3 o'clock (0 radians).
        // Math.cos takes radians.
        var angleInRadians = (angleInDegrees) * Math.PI / 180.0;

        return {
            x: centerX + (radius * Math.cos(angleInRadians)),
            y: centerY + (radius * Math.sin(angleInRadians)) // Y is down in SVG
        };
    }

    createSector(x, y, r1, r2, startAngle, endAngle) {
        // Draw a sector between r1 and r2, from startAngle to endAngle.
        // Arcs in SVG require flag.
        // Angles are in degrees.
        
        // Ensure start < end for logic?
        // Not necessarily.
        
        const start1 = this.polarToCartesian(x, y, r1, startAngle);
        const end1 = this.polarToCartesian(x, y, r1, endAngle);
        const start2 = this.polarToCartesian(x, y, r2, startAngle);
        const end2 = this.polarToCartesian(x, y, r2, endAngle);

        // Large arc flag
        // Calculate diff.
        let diff = endAngle - startAngle;
        if (diff < 0) diff += 360;
        // If calculating standard math way
        
        // Actually since we use our custom toSvgAngle, let's rely on the absolute difference in logic.
        // But toSvgAngle flips direction.
        
        // Let's just use ABS difference for flag?
        // Visually, a sign is 30 degrees. So always small arc (0).
        const largeArcFlag = "0"; 
        
        // Sweep flag? 
        // In SVG: 1 is positive angle direction (CW because Y is down).
        // Our toSvgAngle returns negative for CCW astrology.
        // So if we go from start to end (which is +30 deg astrology), SVG angle decreases.
        // Start: -10, End: -40.
        // Path from Start to End is CCW (visually).
        // So sweep flag 0.
        
        const d = [
            "M", start1.x, start1.y,
            "A", r1, r1, 0, largeArcFlag, 0, end1.x, end1.y,
            "L", end2.x, end2.y,
            "A", r2, r2, 0, largeArcFlag, 1, start2.x, start2.y, // Reverse sweep for inner
            "Z"
        ].join(" ");

        const path = document.createElementNS(this.ns, "path");
        this.safeSetAttr(path, "d", d);
        return path;
    }
}
