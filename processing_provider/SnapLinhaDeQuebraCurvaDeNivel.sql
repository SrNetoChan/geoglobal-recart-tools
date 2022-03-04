/*-- Cria vertices 3D na intersecção com curvas de nível */

/*-- Fazer backup das tabelas originais */

CREATE SCHEMA IF NOT EXISTS backup;

CREATE TABLE backup.linha_de_quebra_bk (like public.linha_de_quebra INCLUDING DEFAULTS);

INSERT INTO backup.linha_de_quebra_bk
SELECT * FROM public.linha_de_quebra;

CREATE TABLE backup.curva_de_nivel_bk (like public.curva_de_nivel INCLUDING DEFAULTS);

INSERT INTO backup.curva_de_nivel_bk
SELECT * FROM public.curva_de_nivel;

/* Criar indices espaciais para melhorar a performance */

CREATE INDEX IF NOT EXISTS linha_de_quebra_geometria_idx ON linha_de_quebra USING gist(geometria);
CREATE INDEX IF NOT EXISTS curva_de_nivel_geometria_idx ON curva_de_nivel USING gist(geometria);

/* Criar tabela com pontos de intersecção entre as camadas para fazer snapping às camadas originais */

CREATE SCHEMA IF NOT EXISTS temp;

DROP TABLE temp.snap_points;
CREATE TABLE temp.snap_points as
SELECT ldq.identificador, 
	cdn.identificador AS cdn_identificador, 
	st_translate(
		st_force3d(
			st_force2d(
				(st_dumppoints(ST_intersection(ldq.geometria,cdn.geometria))).geom))
		,0,	0,st_z(st_startpoint(cdn.geometria))
		) AS geometria
FROM linha_de_quebra ldq 
	JOIN curva_de_nivel cdn ON st_intersects(ldq.geometria,cdn.geometria);

CREATE INDEX ON temp.snap_points(identificador);
CREATE INDEX ON temp.snap_points(cdn_identificador);

/* Fazer snap das geometrias originais às intersecções entre as duas camadas */

WITH points_collect AS (
	SELECT identificador, st_collect(geometria) AS geometria
	FROM temp.snap_points 
	GROUP BY identificador
	)
UPDATE linha_de_quebra AS ldq SET
geometria = st_snap(ldq.geometria, sc.geometria, 0.01)
FROM points_collect AS sc
WHERE ldq.identificador = sc.identificador;

WITH points_collect AS (
	SELECT cdn_identificador, st_collect(geometria) AS geometria
	FROM temp.snap_points 
	GROUP BY cdn_identificador
	)
UPDATE curva_de_nivel AS cdnt SET
geometria = st_snap(cdnt.geometria, sc.geometria, 0.01)
FROM points_collect AS sc
WHERE cdnt.identificador = sc.cdn_identificador;
