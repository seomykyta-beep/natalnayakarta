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

        // Радиусы для двойной карты
        this.rOuterRing = size / 2 - 5;
        this.rTransitOuter = this.rOuterRing - 10;
        this.rTransitInner = this.rTransitOuter - 40;
        
        this.svg = document.createElementNS(this.ns, "svg");
        this.svg.setAttribute("width", size);
        this.svg.setAttribute("height", size);
        this.svg.style.background = "transparent";
        this.svg.style.display = "block";
        this.container.innerHTML = "";
        this.container.appendChild(this.svg);

        this.signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"];
        this.signColors = ["#f26d50","#4caf50","#ffeb3b","#26c6da",
                           "#ef5350","#66bb6a","#ffee58","#26c6da",
                           "#ef5350","#66bb6a","#ffee58","#26c6da"];
        this.glyphColors = {
            Sun: "#ff6d00", Moon: "#444", Mercury: "#111", Venus: "#4caf50",
            Mars: "#e53935", Jupiter: "#1565c0", Saturn: "#6d4c41",
            Uranus: "#00acc1", Neptune: "#3f51b5", Pluto: "#6a1b9a",
            North_node: "#000", South_node: "#000", Lilith: "#000",
            Chiron: "#7b1fa2", ASC: "#c62828", MC: "#1565c0"
        };
        this.planetIcons = {
            Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂",
            Jupiter: "♃", Saturn: "♄", Uranus: "♅", Neptune: "♆", Pluto: "♇",
            North_node: "☊", South_node: "☋", Lilith: "⚸", Chiron: "⚷",
            ASC: "AC", MC: "MC"
        };
    }

    setAttr(el, name, value) {
        if (el) el.setAttribute(name, value);
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

    drawSingleChart(data) {
        this.drawBackground();
        this.drawZodiacRing();
        this.drawHouses(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        if (data.planets) this.drawPlanets(data.planets);
        this.drawInnerCircle();
    }

    drawDualChart(data) {
        const s = this.size;
        this.rOuter = s / 2 - 5;
        this.rTransitOuter = this.rOuter - 10;
        this.rTransitInner = this.rTransitOuter - 45;
        this.rOuterAccent = this.rTransitInner - 5;
        this.rRulerOuter = this.rOuterAccent - 8;
        this.rRulerInner = this.rRulerOuter - 12;
        this.rZodiacOuter = this.rRulerInner - 8;
        this.rZodiacInner = this.rZodiacOuter - 28;
        this.rPlanetBase = this.rZodiacInner - 12;
        this.rAspect = this.rPlanetBase - 40;
        this.rHouseText = this.rAspect - 10;

        this.drawDualBackground();
        this.drawOuterTransitRing(data.outerPlanets);
        this.drawZodiacRing();
        this.drawHouses(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        if (data.planets) this.drawPlanets(data.planets);
        this.drawInnerCircle();
    }

    drawBackground() {
        const bg = document.createElementNS(this.ns, "circle");
        this.setAttr(bg, "cx", this.cx);
        this.setAttr(bg, "cy", this.cy);
        this.setAttr(bg, "r", this.rOuter);
        this.setAttr(bg, "fill", "#f5f5dc");
        this.svg.appendChild(bg);

        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, "cx", this.cx);
        this.setAttr(inner, "cy", this.cy);
        this.setAttr(inner, "r", this.rZodiacInner);
        this.setAttr(inner, "fill", "#fff");
        this.svg.appendChild(inner);
    }

    drawDualBackground() {
        const halo = document.createElementNS(this.ns, "circle");
        this.setAttr(halo, "cx", this.cx);
        this.setAttr(halo, "cy", this.cy);
        this.setAttr(halo, "r", this.rOuter);
        this.setAttr(halo, "fill", "#e0f7fa");
        this.svg.appendChild(halo);

        const transitRing = document.createElementNS(this.ns, "circle");
        this.setAttr(transitRing, "cx", this.cx);
        this.setAttr(transitRing, "cy", this.cy);
        this.setAttr(transitRing, "r", this.rTransitOuter);
        this.setAttr(transitRing, "fill", "#fff");
        this.setAttr(transitRing, "stroke", "#4dd0e1");
        this.setAttr(transitRing, "stroke-width", "2");
        this.svg.appendChild(transitRing);

        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, "cx", this.cx);
        this.setAttr(inner, "cy", this.cy);
        this.setAttr(inner, "r", this.rTransitInner);
        this.setAttr(inner, "fill", "#e6f6d6");
        this.svg.appendChild(inner);

        const white = document.createElementNS(this.ns, "circle");
        this.setAttr(white, "cx", this.cx);
        this.setAttr(white, "cy", this.cy);
        this.setAttr(white, "r", this.rZodiacInner);
        this.setAttr(white, "fill", "#fff");
        this.svg.appendChild(white);
    }

    drawZodiacRing() {
        for (let i = 0; i < 12; i++) {
            const startAngle = (i * 30 + this.rotationOffset) * Math.PI / 180;
            const endAngle = ((i + 1) * 30 + this.rotationOffset) * Math.PI / 180;
            
            const path = document.createElementNS(this.ns, "path");
            const x1 = this.cx + this.rZodiacOuter * Math.cos(startAngle);
            const y1 = this.cy + this.rZodiacOuter * Math.sin(startAngle);
            const x2 = this.cx + this.rZodiacOuter * Math.cos(endAngle);
            const y2 = this.cy + this.rZodiacOuter * Math.sin(endAngle);
            const x3 = this.cx + this.rZodiacInner * Math.cos(endAngle);
            const y3 = this.cy + this.rZodiacInner * Math.sin(endAngle);
            const x4 = this.cx + this.rZodiacInner * Math.cos(startAngle);
            const y4 = this.cy + this.rZodiacInner * Math.sin(startAngle);
            
            const d = `M${x1},${y1} A${this.rZodiacOuter},${this.rZodiacOuter} 0 0,1 ${x2},${y2} L${x3},${y3} A${this.rZodiacInner},${this.rZodiacInner} 0 0,0 ${x4},${y4} Z`;
            this.setAttr(path, "d", d);
            this.setAttr(path, "fill", this.signColors[i]);
            this.setAttr(path, "stroke", "#333");
            this.setAttr(path, "stroke-width", "0.5");
            this.svg.appendChild(path);

            const midAngle = ((i + 0.5) * 30 + this.rotationOffset) * Math.PI / 180;
            const rMid = (this.rZodiacOuter + this.rZodiacInner) / 2;
            const tx = this.cx + rMid * Math.cos(midAngle);
            const ty = this.cy + rMid * Math.sin(midAngle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", tx);
            this.setAttr(text, "y", ty);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", "16");
            this.setAttr(text, "fill", "#333");
            text.textContent = this.signs[i];
            this.svg.appendChild(text);
        }
    }

    drawHouses(houses) {
        for (let i = 0; i < 12; i++) {
            const angle = (houses[i] + this.rotationOffset) * Math.PI / 180;
            const x1 = this.cx + this.rZodiacInner * Math.cos(angle);
            const y1 = this.cy + this.rZodiacInner * Math.sin(angle);
            const x2 = this.cx + this.rAspect * Math.cos(angle);
            const y2 = this.cy + this.rAspect * Math.sin(angle);
            
            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, "x1", x1);
            this.setAttr(line, "y1", y1);
            this.setAttr(line, "x2", x2);
            this.setAttr(line, "y2", y2);
            this.setAttr(line, "stroke", i % 3 === 0 ? "#333" : "#999");
            this.setAttr(line, "stroke-width", i % 3 === 0 ? "2" : "1");
            this.svg.appendChild(line);

            const nextHouse = houses[(i + 1) % 12];
            let midAngle = (houses[i] + nextHouse) / 2;
            if (nextHouse < houses[i]) midAngle = (houses[i] + nextHouse + 360) / 2;
            midAngle = (midAngle + this.rotationOffset) * Math.PI / 180;
            
            const rText = this.rHouseText;
            const tx = this.cx + rText * Math.cos(midAngle);
            const ty = this.cy + rText * Math.sin(midAngle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", tx);
            this.setAttr(text, "y", ty);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", "10");
            this.setAttr(text, "fill", "#666");
            text.textContent = (i + 1).toString();
            this.svg.appendChild(text);
        }
    }

    drawPlanets(planets) {
        const used = [];
        planets.forEach(p => {
            if (!p.abs_pos && p.abs_pos !== 0) return;
            let angle = (p.abs_pos + this.rotationOffset) * Math.PI / 180;
            let r = this.rPlanetBase;

            for (let u of used) {
                const diff = Math.abs(angle - u.angle);
                if (diff < 0.15 || diff > Math.PI * 2 - 0.15) {
                    r -= 18;
                }
            }
            used.push({ angle, r });

            const x = this.cx + r * Math.cos(angle);
            const y = this.cy + r * Math.sin(angle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", x);
            this.setAttr(text, "y", y);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", "14");
            this.setAttr(text, "font-weight", "bold");
            this.setAttr(text, "fill", this.glyphColors[p.key] || "#333");
            text.textContent = this.planetIcons[p.key] || p.icon || "●";
            this.svg.appendChild(text);
        });
    }

    drawOuterTransitRing(planets) {
        if (!planets) return;
        planets.forEach(p => {
            if (!p.abs_pos && p.abs_pos !== 0) return;
            const angle = (p.abs_pos + this.rotationOffset) * Math.PI / 180;
            const r = (this.rTransitOuter + this.rTransitInner) / 2;
            const x = this.cx + r * Math.cos(angle);
            const y = this.cy + r * Math.sin(angle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", x);
            this.setAttr(text, "y", y);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", "12");
            this.setAttr(text, "fill", "#0097a7");
            text.textContent = this.planetIcons[p.key] || p.icon || "●";
            this.svg.appendChild(text);
        });
    }

    drawAspects(aspects, planets) {
        const posMap = {};
        planets.forEach(p => {
            if (p.abs_pos !== undefined) posMap[p.key] = p.abs_pos;
            if (p.name) posMap[p.name] = p.abs_pos;
        });

        const colors = {
            Conjunction: "#4fc3f7", Sextile: "#66bb6a", Square: "#ef5350",
            Trine: "#8bc34a", Opposition: "#ff9100", Quincunx: "#26c6da"
        };

        aspects.forEach(a => {
            const pos1 = posMap[a.p1_key] ?? posMap[a.p1];
            const pos2 = posMap[a.p2_key] ?? posMap[a.p2];
            if (pos1 === undefined || pos2 === undefined) return;

            const angle1 = (pos1 + this.rotationOffset) * Math.PI / 180;
            const angle2 = (pos2 + this.rotationOffset) * Math.PI / 180;
            const r = this.rAspect - 5;
            
            const x1 = this.cx + r * Math.cos(angle1);
            const y1 = this.cy + r * Math.sin(angle1);
            const x2 = this.cx + r * Math.cos(angle2);
            const y2 = this.cy + r * Math.sin(angle2);

            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, "x1", x1);
            this.setAttr(line, "y1", y1);
            this.setAttr(line, "x2", x2);
            this.setAttr(line, "y2", y2);
            this.setAttr(line, "stroke", colors[a.type] || "#ccc");
            this.setAttr(line, "stroke-width", "1");
            this.setAttr(line, "opacity", "0.6");
            this.svg.appendChild(line);
        });
    }

    drawInnerCircle() {
        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, "cx", this.cx);
        this.setAttr(inner, "cy", this.cy);
        this.setAttr(inner, "r", this.rAspect);
        this.setAttr(inner, "fill", "none");
        this.setAttr(inner, "stroke", "#aaa");
        this.setAttr(inner, "stroke-width", "1");
        this.svg.appendChild(inner);
    }
}
