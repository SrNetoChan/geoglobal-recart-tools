/*-- Cria vertices 3D na intersecção com curvas de nível */

/*-- Fazer backup das tabelas originais */

CREATE SCHEMA IF NOT EXISTS backup;

CREATE TABLE backup.seg_via_rodov_bk (like public.seg_via_rodov INCLUDING DEFAULTS);

INSERT INTO backup.seg_via_rodov_bk
SELECT * FROM public.seg_via_rodov;

CREATE TABLE backup.curva_de_nivel_bk (like public.curva_de_nivel INCLUDING DEFAULTS);

INSERT INTO backup.curva_de_nivel_bk
SELECT * FROM public.curva_de_nivel;

/* Criar indices espaciais para melhorar a performance */

CREATE INDEX IF NOT EXISTS seg_via_rodov_geometria_idx ON seg_via_rodov USING gist(geometria);
CREATE INDEX IF NOT EXISTS curva_de_nivel_geometria_idx ON curva_de_nivel USING gist(geometria);

/* Criar tabela com pontos de intersecção entre as camadas para fazer snapping às camadas originais */

CREATE SCHEMA IF NOT EXISTS temp;

DROP TABLE IF EXISTS temp.snap_points;
CREATE TABLE temp.snap_points as
SELECT svr.identificador, 
	cdn.identificador AS cdn_identificador, 
	st_translate(
		st_force3d(
			st_force2d(
				(st_dumppoints(ST_intersection(svr.geometria,cdn.geometria))).geom))
		,0,	0,st_z(st_startpoint(cdn.geometria))
		) AS geometria
FROM seg_via_rodov svr 
	JOIN curva_de_nivel cdn ON st_intersects(svr.geometria,cdn.geometria)
WHERE valor_posicao_vertical_transportes = '0';

CREATE INDEX ON temp.snap_points(identificador);
CREATE INDEX ON temp.snap_points(cdn_identificador);

/* Fazer snap das geometrias originais às intersecções entre as duas camadas */

WITH points_collect AS (
	SELECT identificador, st_collect(geometria) AS geometria
	FROM temp.snap_points 
	GROUP BY identificador
	)
UPDATE seg_via_rodov AS svrt SET
geometria = st_snap(svrt.geometria, sc.geometria, 0.01)
FROM points_collect AS sc
WHERE svrt.identificador = sc.identificador;

WITH points_collect AS (
	SELECT cdn_identificador, st_collect(geometria) AS geometria
	FROM temp.snap_points 
	GROUP BY cdn_identificador
	)
UPDATE curva_de_nivel AS cdnt SET
geometria = st_snap(cdnt.geometria, sc.geometria, 0.01)
FROM points_collect AS sc
WHERE cdnt.identificador = sc.cdn_identificador;

DROP SCHEMA IF EXISTS temp cascade;