/* Original YUGA authoring adapter, CC0-1.0.
 * Calls unmodified Morten S. Mikkelsen MikkTSpace; see vendor source notices.
 * Outputs are PER CORNER, never indexed/averaged by source vertex.
 */
#include <stdint.h>
#include <stddef.h>
#include <math.h>
#include <string.h>
#include "mikktspace.h"

#define YUGA_MAX_VERTICES 2000000u
#define YUGA_MAX_CORNERS 6000000u

typedef struct {
    const float *positions, *normals, *uvs;
    const uint32_t *indices;
    uint32_t corners;
    float *output;
} YugaMikkData;

static int faces(const SMikkTSpaceContext *ctx) {
    return (int)(((const YugaMikkData *)ctx->m_pUserData)->corners/3u);
}
static int vertices(const SMikkTSpaceContext *ctx,int face) { (void)ctx;(void)face;return 3; }
static uint32_t index_at(const SMikkTSpaceContext *ctx,int face,int corner) {
    return ((const YugaMikkData *)ctx->m_pUserData)->indices[(size_t)face*3u+(size_t)corner];
}
static void position(const SMikkTSpaceContext *ctx,float out[],int face,int corner) {
    const YugaMikkData *data=(const YugaMikkData *)ctx->m_pUserData;
    memcpy(out,data->positions+(size_t)index_at(ctx,face,corner)*3u,3u*sizeof(float));
}
static void normal(const SMikkTSpaceContext *ctx,float out[],int face,int corner) {
    const YugaMikkData *data=(const YugaMikkData *)ctx->m_pUserData;
    memcpy(out,data->normals+(size_t)index_at(ctx,face,corner)*3u,3u*sizeof(float));
}
static void texcoord(const SMikkTSpaceContext *ctx,float out[],int face,int corner) {
    const YugaMikkData *data=(const YugaMikkData *)ctx->m_pUserData;
    memcpy(out,data->uvs+(size_t)index_at(ctx,face,corner)*2u,2u*sizeof(float));
}
static void tangent(const SMikkTSpaceContext *ctx,const float v[],float sign,int face,int corner) {
    YugaMikkData *data=(YugaMikkData *)ctx->m_pUserData;
    float *out=data->output+((size_t)face*3u+(size_t)corner)*4u;
    memcpy(out,v,3u*sizeof(float));out[3]=sign;
}

/* Return0=success,1=dimensions/pointers,2=nonfinite/unbounded values,
 *3=index bounds,4=non-unit normals,5=Mikk failure,6=nonfinite output,
 *7=degenerate geometry/UV. Buffer lengths are the caller's responsibility;
 * the Python wrapper validates actual arrays before entering this ABI.
 */
int yuga_mikk_generate(const float *positions,const float *normals,const float *uvs,
                      uint32_t vertex_count,const uint32_t *indices,uint32_t corner_count,
                      float *output,size_t output_float_count) {
    if (!positions||!normals||!uvs||!indices||!output||!vertex_count||
        vertex_count>YUGA_MAX_VERTICES||!corner_count||corner_count>YUGA_MAX_CORNERS||
        corner_count%3u||output_float_count!=(size_t)corner_count*4u) return 1;
    for(uint32_t i=0;i<vertex_count;i++) {
        double length=0.0;
        for(unsigned c=0;c<3;c++) {
            float p=positions[(size_t)i*3u+c],n=normals[(size_t)i*3u+c];
            if(!isfinite(p)||!isfinite(n)||fabsf(p)>1000000.0f) return 2;
            length+=(double)n*(double)n;
        }
        if(fabs(sqrt(length)-1.0)>0.002) return 4;
        for(unsigned c=0;c<2;c++) {
            float u=uvs[(size_t)i*2u+c];if(!isfinite(u)||fabsf(u)>1000000.0f)return 2;
        }
    }
    for(uint32_t i=0;i<corner_count;i++)if(indices[i]>=vertex_count)return 3;
    for(uint32_t i=0;i<corner_count;i+=3u) {
        uint32_t a=indices[i],b=indices[i+1u],c=indices[i+2u];
        double p[3],q[3];
        for(unsigned k=0;k<3;k++) {
            p[k]=(double)positions[(size_t)b*3u+k]-(double)positions[(size_t)a*3u+k];
            q[k]=(double)positions[(size_t)c*3u+k]-(double)positions[(size_t)a*3u+k];
        }
        double x=p[1]*q[2]-p[2]*q[1],y=p[2]*q[0]-p[0]*q[2],z=p[0]*q[1]-p[1]*q[0];
        double s=(double)uvs[(size_t)b*2u]-(double)uvs[(size_t)a*2u];
        double t=(double)uvs[(size_t)b*2u+1u]-(double)uvs[(size_t)a*2u+1u];
        double u=(double)uvs[(size_t)c*2u]-(double)uvs[(size_t)a*2u];
        double v=(double)uvs[(size_t)c*2u+1u]-(double)uvs[(size_t)a*2u+1u];
        if(sqrt(x*x+y*y+z*z)<=1e-12||fabs(s*v-t*u)<=1e-12)return 7;
    }
    YugaMikkData data={positions,normals,uvs,indices,corner_count,output};
    SMikkTSpaceInterface interface={0};
    interface.m_getNumFaces=faces;interface.m_getNumVerticesOfFace=vertices;
    interface.m_getPosition=position;interface.m_getNormal=normal;interface.m_getTexCoord=texcoord;
    interface.m_setTSpaceBasic=tangent;
    SMikkTSpaceContext context={&interface,&data};
    if(!genTangSpaceDefault(&context))return 5;
    for(size_t i=0;i<output_float_count;i++)if(!isfinite(output[i]))return 6;
    return 0;
}
